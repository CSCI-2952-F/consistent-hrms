import json

from nameko.rpc import rpc

from lib import crypto
from lib.hospital import get_hospital_name
from lib.local_storage import LocalStorage

class PhysicianService:
    name = 'physician_service'
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

        # Generate keys for physician.
        pub_key, priv_key = crypto.generate_keys()

        try:
            self.local_storage.add_staff(uid, physician_name)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e

        return uid
        
    
    @rpc
    def read(self, patient_id):
        """
        Returns encrypted medical records for uid.
        Returns an error if the patient has not registered with a hospital.
        """
        med_records = []

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_id)

        # Get the public key from consistent storage if it exists.
        try:
            pub_key = self.consistent_storage.get(hash_uid)
            # Obtain the encrypted medical records.
            med_records = self.local_storage.get_items(hash_uid, pub_key)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e
        
        return med_records

    @rpc
    def write(self, physician_id, patient_id, data):
        """
        Create medical record for patient and put in local storage.
        Return True if successful.
        """
        #TODO: update params to take in patient card, validate card, check that
        # decrypted encrypted uid is the same uid generated from the card 
        # (blockchain attestation), conform data to medical record

        # Check that the physician has registered with this hospital.
        if not self.local_storage.valid_staff(physician_id):
            return False        

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_id)

        # Get the public key from consistent storage if it exists.
        try:
            pub_key = self.consistent_storage.get(hash_uid)
            self.local_storage.insert_item(hash_uid, pub_key, data)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e



    
    
