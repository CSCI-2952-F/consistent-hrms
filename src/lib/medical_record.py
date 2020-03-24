import json
import time

NAME = "name"
PATIENT_ID = "patient_id"
HOSPITAL = "hospital"
DATE = "date"
NOTES = "notes"
SIGNATURE = "signature"

NAME_INDX = 0
PATIENT_ID_INDX = 1
HOSPITAL_INDX = 2
DATE_INDX = 3
NOTES_INDX = 4
SIGNATURE_INDX = 5


class MedicalRecord:
    """
    Standardized medical record format.
    """
    def __init__(self, name, card=None):
        """
        Construct a new MedicalRecord object.
        :param card: Patient card to help populate the basic medical record.
        :param name: Name of entity that is creating the medical record.
        """
        if card:
            self.name = card.patient_name
            self.patient_id = card.patient_id
            self.hospital = card.hospital_name
        else:
            self.name = None
            self.patient_id = None
            self.hospital = None

        # Default set.
        self.date = time.ctime()
        self.notes = None
        self.signature = name

    def restore(self, k, v):
        """
        Before restoring the current medical record with previous information, check that the current medical record does not have this information.
        :param k: Key
        :param v: Value
        """
        if k == NAME:
            if self.name == None:
                self.name = v
        elif k == PATIENT_ID:
            if self.patient_id == None:
                self.patient_id = v
        elif k == HOSPITAL:
            if self.hospital == None:
                self.hospital = v
        elif k == DATE:
            if self.date == None:
                self.date = v
        elif k == NOTES:
            if self.notes == None:
                self.notes = v
        elif k == SIGNATURE:
            if self.signature == None:
                self.signature = v
        else:
            raise Exception("ERROR: unexpected type %s" % k)

    def __str__(self):
        name = str(self.name)
        patient_id = str(self.patient_id)
        hospital = str(self.hospital)
        date = str(self.date)
        notes = str(self.notes)
        signature = str(self.signature)
        result = NAME + ":" + name + "," + PATIENT_ID + ":" + patient_id + "," + HOSPITAL + ":" + hospital + "," + DATE + ":" + date + "," + NOTES + ":" + notes + "," + SIGNATURE + ":" + signature
        return result


def get_medical_record(string):
    """
    Helper function to convert string to medical record object.
    :param: string: Medical record represented as a string.
    :return: Medical record
    """

    components = string.split(",")
    med_rec = MedicalRecord(components[SIGNATURE_INDX].split(":")[1])
    med_rec.name = components[NAME_INDX].split(":")[1]
    med_rec.patient_id = components[PATIENT_ID_INDX].split(":")[1]
    med_rec.hospital = components[HOSPITAL_INDX].split(":")[1]
    med_rec.date = components[DATE_INDX].replace("date:", "")  # Edge case because of how time is represented.
    med_rec.notes = components[NOTES_INDX].split(":")[1]
    return med_rec
