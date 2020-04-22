import sys
import time

import grequests

with open('tests/pub.key') as f:
    PUBLIC_KEY = f.read()


def main():
    if len(sys.argv) != 3:
        print('Usage: python registration_load_test.py [start_id] [end_id]')
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
