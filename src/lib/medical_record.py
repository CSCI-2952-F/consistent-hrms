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
    
    def __str__(self):
        record_to_string = ""
        record_to_string = record_to_string + str(self.name) + ","
        record_to_string = record_to_string + str(self.patient_id) + ","
        record_to_string = record_to_string + str(self.hospital) + ","
        record_to_string = record_to_string + str(self.date) + ","
        record_to_string = record_to_string + str(self.notes) + ","
        record_to_string = record_to_string + str(self.signature)       
        return record_to_string
