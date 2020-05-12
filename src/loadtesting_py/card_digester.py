import csv
import traceback

from sys import exit
from os import chdir
from glob import glob
from copy import deepcopy
from random import shuffle

CARD_PATH = "/usr/src/app/bigchaindb_client/patient_cards/"


def catch_exc(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            tb = traceback.format_exc()
            _debug_print(tb)
            exit(1)

    return wrapper


class PatientCardDigester:
    @catch_exc
    def __init__(self, card_path=None):
        if card_path:
            self.card_path = card_path
        else:
            self.card_path = CARD_PATH

        self.cards = []
        self.unique_cards = []

        self._digest_cards()

    @catch_exc
    def _digest_cards(self):
        chdir(self.card_path)
        for card_file in glob("*.csv"):
            with open(card_file, "r") as f:
                reader = csv.reader(f, delimiter=",", quotechar='"')
                for i, row in enumerate(reader):
                    if i == 0:
                        continue
                    else:
                        name = row[0]
                        patient_id = row[1]
                        pub_key = row[2]
                        priv_key = row[3]

                        self.cards.append(PatientCard(name, patient_id, pub_key, priv_key))
        self.unique_cards = deepcopy(self.cards)

    @catch_exc
    def get_card_without_replacement(self, random=False):
        if random:
            shuffle(self.unique_cards)
        return self.unique_cards.pop()

    @catch_exc
    def get_card_with_replacement(self, random=False):
        if random:
            shuffle(self.cards)
        return self.cards[0]

    @catch_exc
    def get_uuid_pubkey_pairs(self):
        res = []
        for card in self.cards:
            res.append((card.uuid, card.pub_key))
        return res


class PatientCard:
    @catch_exc
    def __init__(self, name, patient_id, pub_key, priv_key):
        self.name = name
        self.patient_id = patient_id
        self.pub_key = pub_key
        self.priv_key = priv_key

        self.uuid = name + patient_id


def _debug_print(msg: str) -> None:
    print(f"[card_digester.py] {msg}", flush=True)
