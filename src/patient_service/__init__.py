import json

from nameko.rpc import RpcProxy, rpc


class PatientService:
    name = 'patient_service'

    consistent_storage = RpcProxy('consistent_storage')

    @rpc
    def healthy(self):
        """
        Returns True if service is healthy.
        """
        return True

    @rpc
    def register(self, patient_id, public_key):
        """
        Registers the patient to this hospital and store the patient's
        public key and patient ID in the consistent storage.
        Returns an error if the patient is already registered in another hospital.
        """
        raise NotImplementedError()
