"""
Helper script that starts Docker Compose namespaces as separate hospitals.
"""

import os
import re
import sys
from subprocess import Popen, PIPE

BASE_FRONTEND_PORT = 8000
BASE_API_GATEWAY_PORT = 8100

DOCKER_COMPOSE_FILE = 'docker-compose.hospital.yml'
HOSPITAL_NAMES_FILE = 'data/hospitals.txt'


def dco(project_name, command_args, env=None):
    if not env:
        env = {}

    args = ['/usr/local/bin/docker-compose', '-f', DOCKER_COMPOSE_FILE]
    if project_name:
        args += ['-p', project_name]
    args += command_args
    command = ' '.join(args)

    env = os.environ.update(env)
    proc = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env, bufsize=1, universal_newlines=True)
    proc.communicate()

    if proc.returncode != 0:
        lines = []
        raise Exception('Command "%s" exited with non-zero exit code (%d)\nOutput:\n%s' % (
            command,
            proc.returncode,
            '\n'.join(lines),
        ))


def main():
    with open(HOSPITAL_NAMES_FILE, 'r') as f:
        for i, line in enumerate(f):
            name = line.strip()
            slug = re.sub('[^a-z]+', '-', name.lower())

            # Prepare ports
            frontend_port = BASE_FRONTEND_PORT + i
            api_gateway_port = BASE_API_GATEWAY_PORT + i

            # Prepare environment
            env = {
                'HOSPITAL_NAME': name,
                'FRONTEND_PORT': str(frontend_port),
                'API_GATEWAY_PORT': str(api_gateway_port),
            }

            # Build and start containers in detached mode
            dco(slug, ['up', '-d', '--build'], env=env)


if __name__ == "__main__":
    main()
