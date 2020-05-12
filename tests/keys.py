import csv
from glob import glob

for card_file in glob("src/bigchaindb_client/patient_cards/*.csv"):
    with open(card_file, "r") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        for i, row in enumerate(reader):
            if i == 0:
                continue
            else:
                PATIENT_NAME = row[0]
                PATIENT_ID = row[1]
                PATIENT_UID = row[2]
                PUBLIC_KEY = row[3]
                PRIVATE_KEY = row[4]
    break
