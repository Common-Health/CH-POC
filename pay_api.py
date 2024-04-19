import json
import base64
from Crypto.Util.Padding import pad
from dotenv import load_dotenv
from Crypto.PublicKey import RSA
from Crypto.Hash import MD5
from Crypto.Signature import pkcs1_15
from Crypto.Cipher import PKCS1_OAEP, AES, PKCS1_v1_5
import os

class encrypt_rsa(): 
    def __init__(self, data):
        # replace with your public key
        load_dotenv()
        key = os.getenv('PUBLIC_KEY')
        public_key = ("-----BEGIN PUBLIC KEY-----\n"+key+"\n-----END PUBLIC KEY-----")
        self.message = data.encode()
        self.public_key = RSA.import_key(public_key)


    # Segmentation encryption
    def encrypt(self):
        try:
            cipher_rsa = PKCS1_v1_5.new(self.public_key)
            res = []
            for i in range(0, len(self.message), 64):
                enc_tmp = cipher_rsa.encrypt(self.message[i:i+64])
                res.append(enc_tmp)
            cipher_text = b''.join(res)
        except Exception as e:
            print(e)
        else:
            return base64.b64encode(cipher_text).decode()

class PrpCrypt(object):
 
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self.key = os.getenv('PRIVATE_KEY')
        if not self.key:
            raise ValueError("No PRIVATE_KEY found in environment variables.")
        self.unpad = lambda date: date[0:-ord(date[-1])]
 
    def aes_cipher(self, aes_str):
        aes = AES.new(self.key.encode('utf-8'), AES.MODE_ECB)
        pad_pkcs7 = pad(aes_str.encode('utf-8'), AES.block_size, style='pkcs7') 
        encrypt_aes = aes.encrypt(pad_pkcs7)
        encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8') 
        encrypted_text_str = encrypted_text.replace("\n", "")
 
        return encrypted_text_str
 
    def decrypt(self, decrData):
        res = base64.decodebytes(decrData.encode("utf8"))
        aes = AES.new(self.key.encode('utf-8'), AES.MODE_ECB)
        msg = aes.decrypt(res).decode("utf8")
        return self.unpad(msg)