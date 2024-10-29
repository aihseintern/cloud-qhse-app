import os

secret_key = os.urandom(24)
print(f"Your secret key: {secret_key.hex()}")