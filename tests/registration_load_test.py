import sys
import time

import grequests

PUBLIC_KEY = """-----BEGIN RSA PUBLIC KEY-----
MIICCgKCAgEAz7/886Se2+xMwaLoPP91oeVagtkDoQzS23J7iM/XcHqQGUrmvn38
0JQeumCvZO5bW+u+TVKbgkG4dKRxEGTNEHLuuTbo+QIUg9O8LMj5s4UtDhEpt7Ij
MLucqtO4BtdiDQ0T9cgjHzu3Weuc8CMgIhbSLa9pcrBEbfTsG+G5sZp5HVuWsmIL
+zbmhIoAO7wjQDo4ZxNVNOXRiFzJU4KCO+fD5HNCdua/Qh4Bg8+jeoRTZyAuYGdw
hCWenGyJJ7We1n9RdCYEKLJMfuulLR6Uxz4OSMrDgGLv4jGTqFdXFDLRe6GgI7ek
7NGjl6n15WH+Pa3wK/gbTx6e+D5W/dFhRe98wp3tSGWTNo1SEqs/3ugG3i1PgL1b
qBVNMZe6Xn0zwPP2dwEc23SD4p/s4DM2z18hX9xSg9hMsVMwyzk6NTcyJgvoMvUG
O0SOZf3CRUVPGPq9eO8F96VJqj1T0jAZ4cf1qqKHx+wphjEjsBzeaMQUsXJ5GF/g
UCmfi1s89Tdm46ECJGilTDQghkuhf2UU7iANRp47/TlGFRZf9ju4U3+kb2tFVF88
vxOBGyh9fI05Puas+nRvBrbyshCURHRVaHt7y6eLFnT0nEThROe7C61Q8+5hcXCM
aBokbnY4AM5z7UhzqIKnS9EVoV9XhLpa0Mrs3+py48d7bylxbhSsOm8CAwEAAQ==
-----END RSA PUBLIC KEY-----"""


def main():
    if len(sys.argv) != 3:
        print('Usage: python consistent_storage_load_test.py [start_id] [end_id]')
        sys.exit(1)

    start_id = int(sys.argv[1])
    end_id = int(sys.argv[2])

    with open('data/hospitals.txt') as f:
        hospitals = [line.strip() for line in f.readlines() if line.strip()]
        num_hospitals = len(hospitals)

    reqs = (
        grequests.post(f'http://localhost:{port}/patient_reg', json={
            'id': str(i),
            'name': f'Patient {i}',
            'pub_key': PUBLIC_KEY,
        }) for port in range(8100, 8100 + num_hospitals) for i in range(start_id, end_id)
    )

    start_time = time.time()
    responses = grequests.map(reqs)
    end_time = time.time()

    # print([res.json() for res in responses])

    # Ensure that the number of successful requests is correct
    num_success = len([1 for res in responses if res.json()['success']])
    if num_success != end_id - start_id:
        print(f'Expected {end_id-start_id} successes, got {num_success} successes')
    else:
        print(f'Correctly got {num_success} successes')

    print(f'Time taken: {end_time-start_time} for {end_id-start_id} requests each at {num_hospitals} hospitals')


if __name__ == "__main__":
    main()
