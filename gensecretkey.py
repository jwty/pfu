# A shortcut script used to generate new secret key hashes

from getpass import getpass
from werkzeug.security import generate_password_hash

secrethash = generate_password_hash(str(getpass('Input new secret key: ')))
print(secrethash)
