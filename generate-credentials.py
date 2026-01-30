# Script to generate SECRET_KEY and ADMIN_PASSWORD config

from getpass import getpass
from secrets import token_urlsafe
from sys import stderr
from werkzeug.security import generate_password_hash

print('Input new admin username: ', end='', file=stderr)
username = input()
password_hash = generate_password_hash(getpass('Input new admin password: ', stream=stderr))

print('Generate new SECRET_KEY? (y/n): ', end='', file=stderr)
generate_secret_key = input().lower() == 'y'

if generate_secret_key:
    secret_key = token_urlsafe(32)
    print(f'SECRET_KEY = "{secret_key}"')
print(f'ADMIN_USERNAME = "{username}"')
print(f'ADMIN_PASSWORD = "{password_hash}"')
