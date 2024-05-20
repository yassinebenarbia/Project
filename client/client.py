import sys
import tensorflow as tf
import gzip
import numpy as np
import gzip

from cryptography.fernet import Fernet
from pyDH import DiffieHellman
import base64

import requests

def capture_photo():
    """
    TODO
    Captures photo from camera

    Returns:
        (image array, image shape)
    """
    pass

def get_photo(path):
    """
    TODO
    Reads photo from the disk

    Returns:
        (image array, image shape)
    """
    img = tf.image.decode_image(tf.io.read_file(path))
    shape = img.shape
    print(shape)
    img = img.numpy().flatten()
    print(img)
    return (img, shape)

class Client:

    def __init__(self, server_ip: str, server_port: str, id: str, device: str, parse_ip = False):
        if parse_ip:
            self.server_ip = sys.argv[2]
        else:
            self.server_ip = server_ip

        self.server_port = server_port
        self.id = id
        self.device = device

    def gen_credintals(self):
        self.dh = DiffieHellman()
        self.pub_key = self.dh.gen_public_key()

        response = requests.get(
                url="http://"+self.server_ip+":"+self.server_port+"/key"
                )
        if response.ok:
            json_rsp = response.json()
            self.server_pubkey = int(json_rsp.get("pubkey"))
            self.secret = self.dh.gen_shared_key(self.server_pubkey)
            self.fernet = Fernet(
                    base64.b64encode(
                        self.secret[:32].encode()
                        )
                    )
            self.id = self.fernet.encrypt(str.encode(self.id))
        else:
            print("Failed to establish credintals!")
            exit(1)

    def share_secret(self):
        response = requests.get(
                url="http://"+self.server_ip+":"+self.server_port+"/",
                json={
                    "pubkey": self.pub_key,
                    "user": self.id.__str__()
                    }
                )
        if response.ok:
            # json_rsp = response.json()
            # self.server_pubkey = int(json_rsp.get("pubkey"))
            # self.secret = self.dh.gen_shared_key(self.server_pubkey)
            # self.fernet = Fernet(base64.b64encode(self.secret[:32].encode()))
            print("secret shared!")
        else:
            exit(1)

    def read_data(self, capture=False, parse_path=False, path=""):
        """
        Reads data to send

        Params:
            capture: either to capture the photo live or to get 
            it from disk
        """
        if capture:
            pass
        if parse_path:
            path = sys.argv[1]
            (img, self.shape) = get_photo(path)
            img = gzip.compress(img)
            self.encrypted_data = self.fernet.encrypt(img)
        else:
            (img, self.shape) = get_photo(path)
            img = gzip.compress(img)
            self.encrypted_data = self.fernet.encrypt(img)

    def send_data(self):
        print("sending...")
        status = requests.post(
                url="http://"+self.server_ip+":"+self.server_port+"/publish",
                json={
                    "data": self.encrypted_data.__str__(),
                    "shape": self.shape.__str__(),
                    "user": self.id.__str__(),
                    "device": self.device.__str__(),
                    },
                timeout=1000000
                )
        if not status.ok:
            print("Error occured while sending the data")
            exit(1)
        else:
            print("data sent sucessfully!")
