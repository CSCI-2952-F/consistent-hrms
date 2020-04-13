"""
Helper script that starts Docker Compose namespaces as separate hospitals.
"""

from __future__ import print_function

import os
import re
import sys
from subprocess import Popen

BASE_FRONTEND_PORT = 8000
BASE_API_GATEWAY_PORT = 8100

DOCKER_COMPOSE_FILE = 'docker-compose.hospital.yml'
HOSPITAL_NAMES_FILE = 'data/hospitals.txt'

PROXIED_COMMANDS = {
    'logs': 'Display logs for containers in each hospital',
    'ps': 'List containers',
    'down': 'Stop and remove containers, networks, images, and volumes (if flags are specified)',
}

TERMCOLOR = {
    'ok': '\033[92m[^]\033[0m',
    'info': '\033[94m[*]\033[0m',
    'warn': '\033[93m[!]\033[0m',
    'error': '\033[91m[#]\033[0m',
}


def get_docker_compose_executable():
    paths = [
        '/usr/local/bin/docker-compose',
        '/usr/bin/docker-compose',
    ]

    for path in paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path

    raise Exception('Could not locate docker-compose. Tried paths: %s' % paths)


def dco(project_name, command_args, env=None):
    if not env:
        env = {}

    docker_compose = get_docker_compose_executable()
    args = [docker_compose, '-f', DOCKER_COMPOSE_FILE]
    if project_name:
        args += ['-p', project_name]
    args += command_args
    command = ' '.join(args)

    print(TERMCOLOR['info'], 'Executing:', command)

    env = os.environ.update(env)
    proc = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env, bufsize=1, universal_newlines=True)

    try:
        proc.communicate()
    except KeyboardInterrupt:
        print(TERMCOLOR['error'], 'Aborting command.')
        return

    if proc.returncode != 0:
        lines = []
        raise Exception('Command "%s" exited with non-zero exit code (%d)\nOutput:\n%s' % (
            command,
            proc.returncode,
            '\n'.join(lines),
        ))


def execute(args):
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
                'HOSPITAL_NAME_SLUG': slug,
                'FRONTEND_PORT': str(frontend_port),
                'API_GATEWAY_PORT': str(api_gateway_port),
            }

            # Build and start containers in detached mode
            dco(slug, args, env=env)


def print_help():
    def print_cmd_help(cmd, desc):
        print('  %s\t\t%s' % (cmd, desc))

    print('This script runs Docker Compose commands for each hospital as specified in data/hospitals.txt.')
    print()
    print('Usage: python hospitals.py COMMAND [OPTIONS]')
    print()
    print('Commands:')
    print_cmd_help('start', 'Builds and starts services')
    print_cmd_help('stop', 'Stop services')
    for cmd, desc in PROXIED_COMMANDS.items():
        print_cmd_help(cmd, desc)
    print_cmd_help('help', 'Display this help message')


def main():

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == 'start':
        execute(['up', '-d', '--build'])

    elif command == 'stop':
        execute(['stop'])

    elif command in PROXIED_COMMANDS:
        execute(sys.argv[1:])

    elif command == 'help':
        print_help()

    else:
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
