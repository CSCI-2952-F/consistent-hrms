import json

from nameko.rpc import rpc

from lib.local_storage import LocalStorage

class PhysicianService:
    name = 'physician_service'

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
        Returns True if registration was successful.
        """

        try:
            LocalStorage.add_staff(physician_id, physician_name)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e

        return True
        
    
    @rpc
    def read(self, patient_uid):
        """
        Returns encrypted medical records for uid.
        Returns an error if the patient has not registered with a hospital.
        """
        med_records = []

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # Get the public key from consistent storage if it exists.
        try:
            pub_key = self.consistent_storage.get(hash_uid)
            # Obtain the encrypted medical records.
            med_records = LocalStorage.get_items(hash_uid, pub_key)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e
        
        return med_records

    @rpc
    def write(self, physician_id, patient_uid, data):
        """
        Create medical record for patient and put in local storage.
        Return True if successful.
        """
        #TODO: update params to take in patient card, validate card, check that
        # decrypted encrypted uid is the same uid generated from the card 
        # (blockchain attestation), conform data to medical record

        # Check that the physician has registered with this hospital.
        if not LocalStorage.valid_staff(physician_id):
            return False        

        # Obtain the hashed UID.
        hash_uid = hasher.hash(patient_uid)

        # Get the public key from consistent storage if it exists.
        try:
            pub_key = self.consistent_storage.get(hash_uid)
            LocalStorage.insert_item(hash_uid, pub_key, data)
        except Exception as e:
            # TODO: Raise relevant exception
            raise e



    
    
