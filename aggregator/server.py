from flask import Flask, request
from cryptography.fernet import Fernet
import base64
import gzip
from pyDH import DiffieHellman
import numpy as np
from addons import (get_yaw, rotate_pose, collect_angles)
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
    pass


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
    array = np.frombuffer(decompressed, dtype=np.uint8)

    client = Client("127.0.0.1", "8080", "u")
    client.gen_credintals()
    client.share_secret()
    client.read_data("venv/assets/tree.jpg")

    processed = process_img(array)
    return processed
#    return "Hi"


if __name__ == '__main__':
#    model = hub.load('https://bit.ly/metrabs_l')  # Takes about 3 minutes
    d1 = DiffieHellman()
    pubkey = d1.gen_public_key()
    app.run(debug=False, port=8081, host='0.0.0.0')
