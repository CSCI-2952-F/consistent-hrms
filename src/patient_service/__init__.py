import base64
import json
import os

import jwt
import jwt.exceptions
import requests
from nameko.exceptions import RemoteError
from nameko.rpc import RpcProxy, rpc

from lib import crypto, hasher
from lib.consistent_storage.base import BaseStorageBackend
from lib.discovery_svc import DiscoveryService
from lib.hospital import get_hospital_name
from lib.local_storage import LocalStorage
from lib.medical_record import MedicalRecord


class Unauthorized(Exception):
    def __init__(self, description):
        super().__init__(f'Unauthorized operation: {description}')


class PatientRegistrationExists(Exception):
    def __init__(self, patient_id):
        super().__init__(f'Patient "{patient_id}" is already registered at "{get_hospital_name()}"')


class PatientRegistrationViolation(Exception):
    def __init__(self, patient_id, hospital_name=None):
        super().__init__(f'Patient "{patient_id}" is already registered at "{hospital_name}"')


class PatientNotRegistered(Exception):
    def __init__(self, patient_id):
        super().__init__(f'Patient "{patient_id}" is not registered at "{get_hospital_name()}"')


class PatientTransferInvalidHospital(Exception):
    def __init__(self, hospital_id):
        super().__init__(f'Cannot transfer to invalid hospital "{hospital_id}"')


class PatientTransferRequestFailed(Exception):
    def __init__(self, hospital_id, error=None):
        msg = f'Oops! Transfer to {hospital_id} has failed.'
        if error:
            msg += ' Error: ' + error
        super().__init__(msg)


class PatientConsistencyViolation(Exception):
    def __init__(self, operation, error):
        super().__init__(f'{operation} was not successful: {error}')


class PatientService:
    name = 'patient_service'
    consistent_storage: BaseStorageBackend = RpcProxy('consistent_storage')
    local_storage = LocalStorage()
    hospital_name = get_hospital_name()
    discovery_svc = DiscoveryService()

    @rpc
    def healthy(self):
        """
        Returns True if service is healthy.
        """
        return True

    @rpc
    def register(self, patient_name, patient_id, pub_key):
        """
        Registers the patient to this hospital and stores the patient's
        public key and patient ID in the consistent storage.
        Raises PatientRegistrationExists if the patient is already registered in this hospital.
        Raises PatientRegistrationViolation if the patient is already registered in another hospital.
        """
        uid = patient_name + patient_id
        hash_uid = hasher.hash(uid)

        # First check if hashed UID resides in consistent storage, and get the owner of the key.
        res = self.consistent_storage.get(hash_uid)
        if res['exists']:
            if res['is_owner']:
                raise PatientRegistrationExists(uid)
            else:
                raise PatientRegistrationViolation(uid, res['owner'])

        # Otherwise, perform a linearizable put request to consistent storage.
        res = self.consistent_storage.put(hash_uid, pub_key)
        if not res['ok']:
            raise PatientRegistrationViolation(uid, res['owner'])

        # Store medical record in local storage
        record = MedicalRecord(self.hospital_name, uid, notes=f'New registration at {self.hospital_name}')
        self.local_storage.insert_item(hash_uid, pub_key, record)

        # Return patient unique identifier
        return uid

    @rpc
    def read(self, patient_uid):
        """
        Returns encrypted medical records for uid.
        Returns an error if the patient has not registered with a hospital.
        """
        med_records = []

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # Obtain the encrypted medical records.
        med_records = self.local_storage.get_items(hash_uid)

        return med_records

    @rpc
    def unregister(self, patient_uid, auth_token):
        """
        Unregisters a patient from this hospital, and removes the patient from consistent storage, and removes all
        patient records from local storage.
        Raises Unauthorized if token is not valid.
        Raises PatientNotRegistered if patient is not registered at this hospital.
        """

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # To perform authorization check, retrieve patient public key from consistent storage.
        res = self.consistent_storage.get(hash_uid)
        if not res['exists'] or not res['value']:
            raise PatientNotRegistered(patient_uid)

        # Verify the token against the patient's public key
        pub_key = res['value']
        if not self._verify_auth_token(pub_key, auth_token):
            raise Unauthorized('missing or invalid token')

        # If not, all good! Remove patient from consistent storage.
        res = self.consistent_storage.remove(hash_uid)
        if not res['removed']:
            raise PatientConsistencyViolation('Remove', res['error'])

        # Delete patient data from local storage.
        self.local_storage.delete_key(hash_uid)

        return True

    @rpc
    def transfer(self, patient_uid, auth_token, dest_hospital):
        """
        Transfers a patient registration from the current hospital to a new one.
        Raises Unauthorized if token is not valid.
        Raises PatientNotRegistered if patient is not registered at this hospital.
        """

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # To perform authorization check, retrieve patient public key from consistent storage.
        res = self.consistent_storage.get(hash_uid)
        if not res['exists'] or not res['value']:
            raise PatientNotRegistered(patient_uid)

        # Verify the token against the patient's public key
        pub_key = res['value']
        if not self._verify_auth_token(pub_key, auth_token):
            raise Unauthorized('missing or invalid token')

        # Look up destination hospital in discovery service
        dest_hospital_info = self.discovery_svc.find_hospital(dest_hospital)
        if dest_hospital_info is None:
            raise PatientTransferInvalidHospital(dest_hospital)

        # Make sure we are not transferring to ourselves.
        if dest_hospital_info['id'] == self.discovery_svc.get_id():
            raise PatientTransferInvalidHospital(dest_hospital)

        # If not, all good! Transfer patient in consistent storage.
        res = self.consistent_storage.transfer(hash_uid, dest_hospital)
        if not res['transferred']:
            raise PatientConsistencyViolation('Transfer', res['error'])

        # Now we actually transfer the encrypted patient data to the target hospital.
        # TODO: Maybe make this part of the request asynchronous? (i.e. push onto a work queue)

        # Add a new record for patient to signify the transfer to a new hospital
        dest_hospital_name = dest_hospital_info['name']
        transfer_record = MedicalRecord(self.hospital_name, patient_uid, notes=f'Transferred to {dest_hospital_name}')
        self.local_storage.insert_item(hash_uid, pub_key, transfer_record)

        # Retrieve private key from discovery service
        hospital_id = self.discovery_svc.get_id()
        priv_key = self.discovery_svc.get_private_key()

        # Serialize and encode all patient data
        records = self.local_storage.get_items(hash_uid)
        data = json.dumps(records)
        encoded = base64.b64encode(data.encode('utf-8'))

        # Sign the encoded data to get a signature
        signature = crypto.sign(encoded, crypto.load_privkey(priv_key)).hex()

        # Send out the transfer request to the target hospital
        addr = dest_hospital_info['gateway_addr']
        url = f'http://{addr}/transfer_request'
        payload = {
            'hospital_id': hospital_id,
            'uid': patient_uid,
            'data': encoded.decode('utf-8'),
            'signature': signature,
        }

        try:
            res = requests.post(url, json=payload)
            res.raise_for_status()
        except requests.HTTPError as e:
            # If there's an error raised here, unfortunately the transfer
            # cannot be rolled back. If only we had actual sagas here...
            # In this case, the patient's data is still in this hospital even though
            # the destination hospital now owns the patient registration.
            if res.json().get('error'):
                raise PatientTransferRequestFailed(dest_hospital, res.json().get('error'))
            raise PatientTransferRequestFailed(dest_hospital, str(e))

        # Make sure that response is valid
        res = res.json()
        success = res.get('success')
        if not success:
            raise PatientTransferRequestFailed(dest_hospital, res.get('error'))

        # Now we can remove the patient from our local storage
        self.local_storage.delete_key(hash_uid)

        return True

    @rpc
    def transfer_request(self, hospital_id, patient_uid, patient_data, signature):
        """
        This RPC handler is invoked by another hospital to receive a transfer request for a patient.
        """

        patient_data = patient_data.encode('utf-8')

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # Make sure that we are actually the owner of the patient uid.
        # NOTE: This cannot be achieved with sagas, because different hospitals have a different
        #       view of the consistent storage state, and thus it is possible for the receiving
        #       hospital (i.e. this hospital) to not yet be the owner of the key at the time
        #       that this request is received.
        #       We shall just ignore this check, since there is no actual violation if we transfer
        #       encrypted patient data without actually transferring ownership of the key.
        # if not self.consistent_storage.get(hash_uid)['is_owner']:
        #     raise PatientNotRegistered(patient_uid)

        # If the patient already has data in our local storage, abort.
        items = self.local_storage.get_items(hash_uid)
        if items:
            raise Unauthorized('patient data exists')

        # Look up hospital in discovery service
        hospital_info = self.discovery_svc.find_hospital(hospital_id)
        if hospital_info is None:
            raise PatientTransferInvalidHospital(hospital_id)

        # Get public key of hospital and verify signature
        pub_key = hospital_info['public_key']
        if not crypto.verify(patient_data, signature, crypto.load_pubkey(pub_key)):
            raise Unauthorized('cannot verify transfer request')

        # Load patient data into local storage.
        decoded = base64.b64decode(patient_data).decode('utf-8')
        records = json.loads(decoded)
        self.local_storage.load_items(hash_uid, records)

        # Return successful response to caller to complete the transfer.
        return True

    def _verify_auth_token(self, pub_key, auth_token) -> bool:
        """
        Verifies an auth token, which is a RS256 JWT signed with a private key only owned by a patient.
        Uses the provided public key to verify the signature and validity of the token.
        """
        try:
            jwt.decode(auth_token, pub_key, algorithms=['RS256'])
            return True
        except jwt.exceptions.DecodeError:
            return False
