import json
import time

class MedicalRecord:
    """
    Standardized medical record format.
    """
    def __init__(self, name, uid):
        """
        Construct a new MedicalRecord object.
        :param name: Name of entity that is creating the medical record.
        :param uid: Patient uid..
        """

        self.date = time.ctime()
        self.notes = None
        self.signature = name
        self.uid = card.uid        
    
    def __str__(self):
        record_to_string = ""
        record_to_string = record_to_string + str(self.uid) + ","
        record_to_string = record_to_string + str(self.date) + ","
        record_to_string = record_to_string + str(self.notes) + ","
        record_to_string = record_to_string + str(self.signature)       
        return record_to_string
