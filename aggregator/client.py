import tensorflow as tf
import gzip
import numpy as np
import gzip

from cryptography.fernet import Fernet
from pyDH import DiffieHellman
import base64

import requests


class Client:

    def __init__(self, server_ip: str, server_port: str, id: str):
        self.server_ip = server_ip
        self.server_port = server_port
        self.id = id

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
            self.id = self.fernet.encrypt(self.id)
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

    def read_data(self, img_array, shape, img_movenet, img_category, device):
        img = img_array
        self.shape = shape
        print("img:", img)
        print("shape:", self.shape)
        img = gzip.compress(img.flatten())
        self.encrypted_data = self.fernet.encrypt(img)
        self.movenet_data = img_movenet
        self.category = img_category
        self.device = device
        print("done!")

    def send_data(self):
        print("sending...")
        status = requests.post(
                url="http://"+self.server_ip+":"+self.server_port+"/publish",
                json={
                    "data": self.encrypted_data.__str__(),
                    "shape": self.shape.__str__(),
                    "user": self.id.__str__(),
                    "device": self.device.__str__(),
                    "movenet": self.movenet_data.__str__(),
                    "category": np.array2string(self.category, separator=", "),
                    },
                timeout=1000000
                )
        if not status.ok:
            print("Error occured while sending the data")
            exit(1)
        else:
            print("data sent sucessfully!")
