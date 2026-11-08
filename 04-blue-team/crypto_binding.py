import os, sys, base64, logging
import cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

HERE = os.path.dirname(os.path.abspath(__file__))
PRIV = os.path.join(HERE, 'agent_private.pem')
PUB = os.path.join(HERE, 'agent_public.pem')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def generate_keys():
    key = Ed25519PrivateKey.generate()
    with open(PRIV, 'wb') as f:
        f.write(key.private_bytes(serialization.Encoding.PEM,
                                  serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption()))
    os.chmod(PRIV, 0o600)
    with open(PUB, 'wb') as f:
        f.write(key.public_key().public_bytes(serialization.Encoding.PEM,
                                              serialization.PublicFormat.SubjectPublicKeyInfo))
    print('Python cryptography library version:', cryptography.__version__)
    print('Ed25519 key pair generated:')
    print('  private key ->', PRIV)
    print('  public key  ->', PUB)

def sign_message(message):
    with open(PRIV, 'rb') as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    return base64.b64encode(key.sign(message.encode())).decode()

def verify_message(message, signature):
    if not signature:
        logging.error('REJECTED: missing signature')
        return False
    with open(PUB, 'rb') as f:
        pub = serialization.load_pem_public_key(f.read())
    try:
        pub.verify(base64.b64decode(signature), message.encode())
        logging.info('Signature verified: message accepted')
        return True
    except (InvalidSignature, ValueError):
        logging.error('REJECTED: signature verification failed (message tampered or forged)')
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'generate':
        generate_keys()
    else:
        msg = 'FROM: orchestrator: run lookup_order(1001)'
        sig = sign_message(msg)
        print('Original message :', msg)
        print('Signature (b64)  :', sig[:40] + '...')
        verify_message(msg, sig)
        tampered = msg.replace('1001', '1002')
        print('Tampered message :', tampered, '(one character changed)')
        verify_message(tampered, sig)
