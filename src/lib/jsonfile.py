import json
import os
import re


def touch(filepath):
    "Touches and ensures a valid JSON file at the given path."

    # Ensure path
    os.makedirs(os.path.abspath(os.path.dirname(filepath)), exist_ok=True)

    # Touch file to make sure it exists
    open(filepath, 'a+').close()

    # Ensure that file is a valid JSON
    with open(filepath, 'r+') as f:
        try:
            json.load(f)
        except json.JSONDecodeError:
            # If not, write an empty JSON object
            f.seek(0)
            json.dump({}, f)
            f.truncate()


def get_path(filepath, jsonpath, separators="/"):
    "Retrieves a given value at a given JSONPath from a JSON file at filepath."

    if separators:
        jsonpaths = re.split(separators, jsonpath)
    else:
        jsonpaths = [jsonpath]

    with open(filepath) as f:
        val = json.load(f)

        for key in jsonpaths:
            if not isinstance(val, dict) or key not in val:
                raise KeyError('%s not in JSON object: %s' % (key, json.dumps(val)))
            val = val[key]

        return val


def get_value(filepath, key):
    "Retrieves a value from JSON object from a JSON file at filepath."

    return get_path(filepath, key, separators=None)


def set_path(filepath, jsonpath, value, separators="/"):
    "Sets a JSON value at the JSONPath in the JSON file and saves the file."

    if separators:
        jsonpaths = re.split(separators, jsonpath)
    else:
        jsonpaths = [jsonpath]

    with open(filepath, 'r+') as f:
        data = json.load(f)
        f.seek(0)

        val = data
        for i, key in enumerate(jsonpaths):
            if not isinstance(val, dict) or key not in val:
                val[key] = {}

            if i == len(jsonpaths) - 1:
                val[key] = value
            else:
                val = val[key]

        json.dump(data, f, indent=2)
        f.truncate()


def set_value(filepath, key, value):
    "Sets a JSON value in the JSON file and saves the file."

    return set_path(filepath, key, value, separators=None)


def delete_path(filepath, jsonpath, separators="/"):
    "Deletes the values rooted at a given JSONPath from a JSON file at filepath."

    if separators:
        jsonpaths = re.split(separators, jsonpath)
    else:
        jsonpaths = [jsonpath]

    deleted = True

    with open(filepath, 'r+') as f:
        data = json.load(f)
        val = data

        for i, key in enumerate(jsonpaths):
            if not isinstance(val, dict) or key not in val:
                deleted = False
                break

            if i == len(jsonpaths) - 1:
                del val[key]
            else:
                val = val[key]

        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

    return deleted


def delete_value(filepath, key):
    "Deletes a key from a JSON object from a JSON file at filepath."

    return delete_path(filepath, key, separators=None)
