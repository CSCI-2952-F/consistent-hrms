from json import JSONEncoder

from lib import crypto


class Card(dict):
    """
    Card created by the hospital.
    """
    def __init__(self, name, uid, priv_key, hospital_name):
        """
        Construct a new Card object.
        :param name: client name
        :param uid: client UID
        :param priv_key: client private key
        :param hospital_name: Name of the hospital
        """

        self.name = name
        self.uid = uid
        self.priv_key = priv_key
        self.hospital_name = hospital_name

        self.update({
            "name": self.name,
            "uid": self.uid,
            "priv_key": crypto.b64encode(self.priv_key),
            "hospital_name": self.hospital_name,
        })
