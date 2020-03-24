class Card:
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

    def __str__(self):
        card_to_string = ""
        card_to_string = card_to_string + str(self.patient_name) + ","
        card_to_string = card_to_string + str(self.patient_id) + ","
        card_to_string = card_to_string + str(self.uid) + ","
        card_to_string = card_to_string + str(self.priv_key) + ","
        card_to_string = card_to_string + str(self.hospital_name)
        return card_to_string
