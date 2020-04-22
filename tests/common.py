import requests


def succeed(url, json):
    res = requests.post(url, json=json)

    if res.status_code != requests.codes.ok:
        raise Exception(f'HTTP error {res.reason} text={res.text}')

    data = res.json()
    if not data['success']:
        raise Exception('Request not successful')

    return data


def fail(url, json):
    res = requests.post(url, json=json)

    if res.status_code != requests.codes.server_error:
        raise Exception(f'Expected exception, got status {res.status_code} text={res.text}')

    data = res.json()
    if data['success']:
        raise Exception(f'Request not supposed to be successful: {data}')

    return data
