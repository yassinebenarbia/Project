from flask import Flask, request
from cryptography.fernet import Fernet
import base64
import gzip
from pyDH import DiffieHellman
import numpy as np
from addons import (get_yaw, rotate_pose, collect_angles)
from movenet import (use_movenet, use_classifier, load_movenet, load_classifier)
from client import Client
import tensorflow_hub as hub


keypoints_name = 'human4d_32'
ground_truth_angle = 90

app = Flask(__name__)

# Example user credentials
users = {
    "user_name": "password_hash"
}

def calculate_score(processed_image):
    """
    Calculate score
    """
    pass


def publish_results():
    """"
    Publish the calculated results to a MQTT server
    """


def process_img(img):
    pred = model.detect_poses(img, skeleton=keypoints_name)
    yaw = get_yaw(pred['poses3d'])
    rotated = rotate_pose(pred['poses3d'], 0)
    angles = collect_angles(rotated)
    result = {
            "pose": rotated,
            "angles": angles
            }
    return result

def send_processed(processed):
    pass

@app.route('/key', methods=['GET'])
def announce():
    return {"pubkey": pubkey.__str__()}

@app.route('/', methods=['GET', 'POST'])
def establish():
    json_body_request = request.get_json()
    print("values: ", request.get_json())
    end_pubkey = json_body_request.get("pubkey")
    end_name = json_body_request.get("user")
    global shared_secret
    shared_secret = d1.gen_shared_key(int(end_pubkey))
    f = Fernet(
            base64.b64encode(
                shared_secret[:32].encode()
                )
            )
    end_name = f.decrypt(end_name[2:-1].encode())
    users[end_name] = shared_secret
    print("shared secret: ", shared_secret)
    return {"pubkey": pubkey.__str__()}


@app.route('/publish', methods=['GET', 'POST'])
def process():
    json_body_request = request.get_json()
    data = json_body_request.get("data")
    user = json_body_request.get("user")
    shape = eval(json_body_request.get("shape"))
    device = eval(json_body_request.get("device"))

    if shared_secret == b'':
        exit(1)
    else:
        f = Fernet(
                base64.b64encode(
                    shared_secret[:32].encode()
                    )
                )
        user = f.decrypt(user[2:-1].encode())

    secret = users.get(user)
    fernet = Fernet(base64.b64encode(secret[:32].encode()))
    decrypted_data = fernet.decrypt(data[2:-1].encode())
    decompressed = gzip.decompress(decrypted_data)
    data_array = np.frombuffer(decompressed, dtype=np.uint8)
    print("data array:", data_array)
    pose = use_movenet(np.reshape(data_array, shape), model)
    category = use_classifier(pose, classifier)

    return "Hi"


# This script will run under the raspberry
if __name__ == '__main__':

    print("""
    This File is meant to run on the client side
    """)
    client = Client("192.168.1.212", "8081", "user", "4", parse_ip=True)
    client.gen_credintals()
    client.share_secret()
    client.read_data(parse_path=True)
    client.send_data()
