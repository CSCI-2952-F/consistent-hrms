package main

import (
	"context"
	"time"

	"gopkg.in/confluentinc/confluent-kafka-go.v1/kafka"
)

type Producer struct {
	*kafka.Producer
}

type Consumer struct {
	*kafka.Consumer
}

func (c *Consumer) ReadC(ctx context.Context, timeout time.Duration) <-chan *kafka.Message {
	msgChan := make(chan *kafka.Message)

	go func() {
		for {
			// Check if context is canceled, if so close the channel
			select {
			case <-ctx.Done():
				close(msgChan)
				return

			default:
			}

			// Otherwise read a message; this also acts as a heartbeat
			msg, err := c.ReadMessage(timeout)
			if err != nil {
				continue
			}
			if msg == nil {
				continue
			}

			// Only send non-nil messages
			msgChan <- msg
		}
	}()

	return msgChan
}
