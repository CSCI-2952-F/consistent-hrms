from json import JSONEncoder

from lib import crypto


class Card(dict):
    """
    Card created by the hospital.
    """
    def __init__(self, patient_name, patient_id, uid, priv_key, hospital_name):
        """
        Construct a new Card object.
        :param patient_name: Name of the patient
        :param patient_id: Id of the patient
        :param uid: Patient uid
        :param priv_key: Patient private key
        :param hospital_name: Name of the hospital
        """

        self.patient_name = patient_name
        self.patient_id = patient_id
        self.uid = uid
        self.priv_key = priv_key
        self.hospital_name = hospital_name

        self.update({
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "uid": self.uid,
            "priv_key": crypto.b64encode(self.priv_key),
            "hospital_name": self.hospital_name,
        })
