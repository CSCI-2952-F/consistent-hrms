import json
import base64
from nameko.exceptions import RemoteError
from nameko.rpc import RpcProxy, rpc

from lib import hasher
from lib.hospital import get_hospital_name
from lib.local_storage import LocalStorage
from lib.medical_record import MedicalRecord


class PatientRegistrationExists(Exception):
    def __init__(self, patient_id):
        super().__init__(f'Patient "{patient_id}" is already registered')


class PatientRegistrationViolation(Exception):
    def __init__(self, patient_id, hospital_name=None):
        super().__init__(f'Patient "{patient_id}" is already registered at "{hospital_name}"')


class PatientService:
    name = 'patient_service'
    consistent_storage = RpcProxy('consistent_storage')
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
                raise PatientRegistrationExists(patient_id)
            else:
                raise PatientRegistrationViolation(patient_id, res['owner'])

        # Otherwise, perform a linearizable put request to consistent storage.
        res = self.consistent_storage.put(hash_uid, pub_key)
        if not res['ok']:
            raise PatientRegistrationViolation(patient_id, res['owner'])

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
