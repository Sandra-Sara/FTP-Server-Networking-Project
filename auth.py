import json
import os
import hashlib
import binascii

USERS_FILE = "users.json"

# -----------------------------
# Load all users
# -----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# -----------------------------
# Save users (if needed)
# -----------------------------
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# -----------------------------
# Hash password using PBKDF2
# -----------------------------
def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)

    hashed = hashlib.pbkdfd2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000
    )

    return binascii.hexlify(salt).decode(), binascii.hexlify(hashed).decode()

# -----------------------------
# Verify password
# -----------------------------
def verify_password(password: str, salt_hex: str, stored_hash_hex: str):
    salt = binascii.unhexlify(salt_hex)
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        100000
    )

    return binascii.hexlify(new_hash).decode() == stored_hash_hex

# -----------------------------
# Authenticate user
# -----------------------------
def authenticate(username, password):
    users = load_users()

    if username not in users:
        return False, None

    info = users[username]

    if verify_password(password, info["salt"], info["password_hash"]):
        return True, info["home"]
    else:
        return False, None
