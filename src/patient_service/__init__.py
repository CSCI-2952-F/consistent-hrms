import base64
import json

import jwt
import jwt.exceptions
from nameko.exceptions import RemoteError
from nameko.rpc import RpcProxy, rpc

from lib import hasher
from lib.consistent_storage import BaseStorageBackend
from lib.hospital import get_hospital_name
from lib.local_storage import LocalStorage
from lib.medical_record import MedicalRecord


class Unauthorized(Exception):
    def __init__(self):
        super().__init__(f'Unauthorized operation; missing or invalid token')


class PatientRegistrationExists(Exception):
    def __init__(self, patient_id):
        super().__init__(f'Patient "{patient_id}" is already registered as "{get_hospital_name()}"')


class PatientRegistrationViolation(Exception):
    def __init__(self, patient_id, hospital_name=None):
        super().__init__(f'Patient "{patient_id}" is already registered at "{hospital_name}"')


class PatientNotRegistered(Exception):
    def __init__(self, patient_id):
        super().__init__(f'Patient "{patient_id}" is not registered at "{get_hospital_name()}"')


class PatientConsistencyViolation(Exception):
    def __init__(self, operation, error):
        super().__init__(f'{operation} was not successful: {error}')


class PatientService:
    name = 'patient_service'
    consistent_storage: BaseStorageBackend = RpcProxy('consistent_storage')
    local_storage = LocalStorage()
    hospital_name = get_hospital_name()

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
        record = MedicalRecord(self.hospital_name, uid)
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
            raise Unauthorized()

        # If not, all good! Remove patient from consistent storage.
        res = self.consistent_storage.remove(hash_uid)
        if not res['removed']:
            raise PatientConsistencyViolation('Remove', res['error'])

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
            raise Unauthorized()

        # If not, all good! Transfer patient
        res = self.consistent_storage.transfer(hash_uid, dest_hospital)
        if not res['transferred']:
            raise PatientConsistencyViolation('Transfer', res['error'])

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
