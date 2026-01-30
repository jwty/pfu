# Script to generate SECRET_KEY and admin credentials

from getpass import getpass
from secrets import token_urlsafe
from werkzeug.security import generate_password_hash

username = input('Input new admin username: ')
password_hash = generate_password_hash(getpass('Input new admin password: '))
generate_secret_key = input('Generate new SECRET_KEY? (y/n): ').lower() == 'y'

print('\nconfig.toml:\n')

if generate_secret_key:
    secret_key = token_urlsafe(32)
    print(f'SECRET_KEY = "{secret_key}"')
print(f'ADMIN_USERNAME = "{username}"')
print(f'ADMIN_PASSWORD = "{password_hash}"')

print('\ndocker-compose.yml environment variables with escaped password hash:\n')
if generate_secret_key:
    print(f'"PFU_SECRET_KEY={secret_key}"')
print(f'"PFU_ADMIN_USERNAME={username}"')
print(f'"PFU_ADMIN_PASSWORD={password_hash.replace("$", "$$")}"')
