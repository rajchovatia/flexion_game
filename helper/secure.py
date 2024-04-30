import hashlib

def custom_hasher(data):
    # Convert data to bytes
    data_bytes = bytes(data, 'utf-8')
    
    # Calculate hash using SHA-256 algorithm
    hash_value = hashlib.sha256(data_bytes).hexdigest()
    
    return hash_value