"""
Our implementation of the Sagas design pattern using Apache Kafka as the shared message bus.
This contains the library code for interacting with Kafka and exposes a KV-store API for
ConsistentStorageProxy can proxy incoming requests to.
"""

import asyncio
import json
import os
import uuid
from threading import Thread

from confluent_kafka import Consumer, KafkaException, Producer

from consistent_storage.sagas.partitions import get_partition
from consistent_storage.sagas.persistent_file import PersistentSagasFileStorage

TOPIC_NAME = os.getenv('SAGAS_TOPIC_NAME')
if not TOPIC_NAME:
    raise Exception('SAGAS_TOPIC_NAME not set')

NUM_PARTITIONS = os.getenv('SAGAS_NUM_PARTITIONS')
if not NUM_PARTITIONS:
    raise Exception('SAGAS_NUM_PARTITIONS not set')
try:
    NUM_PARTITIONS = int(NUM_PARTITIONS)
except ValueError as e:
    raise Exception('SAGAS_NUM_PARTITIONS is not a valid integer')
if NUM_PARTITIONS <= 0:
    raise Exception('SAGAS_NUM_PARTITIONS must be a positive integer')

# Path to persistent file-backed storage
PERSISTENCE_FILE_PATH = '/var/lib/sagas/data.json'


class SagasStorage:
    def __init__(self, loop=None):
        brokers = 'kafka:9092'

        # Initialize persistent storage
        self.storage = PersistentSagasFileStorage(PERSISTENCE_FILE_PATH)

        # Consumer group has to be unique within the topic.
        # We also use this to identify the producer of a message.
        # The most foolproof way is to use a centralized naming/assignment registry.
        # However, we will just generate a (persistent) random group ID and hope for no collisions.
        self.group_id = self.storage._get('group_id')
        if not self.group_id:
            self.group_id = str(uuid.uuid1())
            self.storage._set('group_id', self.group_id)

        # Initialize Kafka producer and consumer
        self.p = Producer({'bootstrap.servers': brokers, 'acks': 'all'})
        self.c = Consumer({'group.id': self.group_id, 'bootstrap.servers': brokers, 'enable.auto.commit': False})
        self.c.subscribe([TOPIC_NAME])

        # Start asyncio event loop
        self._loop = loop or asyncio.get_event_loop()
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._producer_waiters = {}
        self._consumer_results = {}

    def stop(self):
        self._cancelled = True
        self._poll_thread.join()

    def get(self, key: str):
        raise NotImplementedError()

    async def put(self, key: str, value: str) -> bool:
        """
        PUT will return only once the written offset has been consumed.
        This ensures linearizability of PUT operations over the entire cluster.
        Returns True if the PUT operation was successful, or False if unsuccessful.
        """

        # Compute partition for key
        partition = get_partition(key, NUM_PARTITIONS)

        # Pass our group ID in the msg headers, to identify the producer of a message
        # TODO: Come up with a non-forgeable scheme so that malicious clients
        #       cannot forge the "owner" header.
        headers = {'owner': self.group_id}

        # Publish message and get offset
        try:
            offset = await self._produce(
                key=key,
                value=json.dumps(value),
                partition=partition,
                headers=headers,
            )
        except Exception as e:
            # Got KafkaException, unable to publish to broker
            # Raise the exception back to caller
            # TODO Check type
            print(e)
            raise e

        # Check if we already consumed and processed this offset, otherwise
        # wait for a signal when it exists.
        if self._consumer_results.get((partition, offset)) is None:
            event = self._create_event(partition, offset)
            await event.wait()

        # The result of the consumer processing corresponds to whether a PUT operation is successful.
        result = self._consumer_results.get((partition, offset))

        if result is None:
            raise Exception('We should have a result after waiting for event')

        return result

    async def _produce(self, **kwargs):
        # Create future for produced message's offset
        result = self._loop.create_future()

        def ack(err, msg):
            if err:
                self._loop.call_soon_threadsafe(result.set_exception, KafkaException(err))
            else:
                self._loop.call_soon_threadsafe(result.set_result, msg.offset())

        # Produce to Kafka topic asynchronously
        self.p.produce(TOPIC_NAME, on_delivery=ack, **kwargs)

        # Await produced offset
        offset = await result

        return offset

    def remove(self, key: str):
        raise NotImplementedError()

    def _poll_loop(self):
        while not self._cancelled:
            self.p.poll(0.1)
            msg = self.c.poll(0.1)
            if msg is not None:
                self._consume(msg)

    def _consume(self, msg):
        if msg.error():
            print(f'Consumer error: {msg.error()}')
            return

        headers = {}
        for k, v in msg.headers():
            headers[k] = v

        key = msg.key()
        value = msg.value()
        partition = msg.partition()
        offset = msg.offset()
        owner = headers['owner']

        print(f'Consumed message: partition={partition} offset={offset} key={key} value={value} owner={owner}')

        # Get existing data for key in storage
        orig, meta = self.storage.retrieve(key)
        result = False

        if orig is None and value is not None:
            # Only store if no other value exists for key at this point.
            self.storage.store(key, json.loads(value), offset, owner)
            result = True
            print(f'Consumer stored key "{key}')

        elif orig is not None and value is None:
            # Only allow owners of a key to delete the key.
            if meta['owner'] == self.group_id:
                self.storage.remove(key, offset, owner)
                result = True
                print(f'Consumer removed key "{key}')
            else:
                print(f'Consumer no-op for DEL "{key}')

        else:
            # All other cases are a no-op.
            print('Consumer no-op')

        # Store result of processing consumer message
        self._consumer_results[(partition, offset)] = result

        # Send signal to any waiters in this (partition, offset) tuple.
        # If there are no waiters, either this client did not produce the msg,
        # or the producer has not yet created the Event. The latter case is fine,
        # because the producer can just read the results directly.
        if self._producer_waiters.get((partition, offset)):
            self._producer_waiters[(partition, offset)].set()

        # Commit offset ONLY after storing locally.
        # Note that auto offset commit is disabled. This provides the strongest, exactly-once semantic guarantees.
        self.c.commit(offsets=[offset])

    def _create_event(self, partition, offset):
        if self._producer_waiters.get((partition, offset)):
            raise Exception('Invariant violation')

        event = asyncio.Event(loop=self._loop)
        self._events[(partition, offset)] = event
        return event
