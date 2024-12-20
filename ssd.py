from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def generate_vapid_keys():
    # Generate a new private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Generate the corresponding public key
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Base64 URL-encode the keys
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode("utf-8").rstrip("=")
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode("utf-8").rstrip("=")

    return public_key_b64, private_key_b64


if __name__ == "__main__":
    public_key, private_key = generate_vapid_keys()
    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")
