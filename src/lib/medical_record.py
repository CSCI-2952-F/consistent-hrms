import json
import time

class MedicalRecord:
    """
    Standardized medical record format.
    """
    def __init__(self, name, card):
        """
        Construct a new MedicalRecord object.
        :param card: Patient card to help populate the basic medical record.
        :param name: Name of entity that is creating the medical record.
        """
        
        self.name = card.patient_name
        self.patient_id = card.patient_id
        self.hospital = card.hospital_name

        # Default set.
        self.date = time.ctime()
        self.notes = None
        self.signature = name
