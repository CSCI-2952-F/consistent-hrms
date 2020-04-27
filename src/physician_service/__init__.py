import json

from nameko.exceptions import RemoteError
from nameko.rpc import RpcProxy, rpc

from lib import hasher
from lib.consistent_storage import BaseStorageBackend
from lib.hospital import get_hospital_name
from lib.local_storage import LocalStorage
from lib.medical_record import MedicalRecord

class PhysicianService:
    name = 'physician_service'
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
    def register(self, physician_name, physician_id):
        """
        Registers the physician to this hospital. A physician can register
        with more than 1 hospital.
        """
        uid = physician_name + physician_id

        self.local_storage.add_staff(uid, physician_name)

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
    def write(self, physician_uid, patient_uid, data):
        """
        Create medical record for patient and put in local storage.
        Return True if successful.
        """

        # Check that the physician has registered with this hospital.
        if not self.local_storage.valid_staff(physician_uid):
            return False

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # Get the public key from consistent storage if it exists.
        pub_key = self.consistent_storage.get(hash_uid)
        self.local_storage.insert_item(hash_uid, pub_key, data)
