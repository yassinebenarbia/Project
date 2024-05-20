from flask import Flask, request
from cryptography.fernet import Fernet
import base64
import gzip
from pyDH import DiffieHellman
import numpy as np
import paho.mqtt.client as mqtt
import json
# from paho.mqtt.client import CallbackAPIVersion
from addons import (evaluate_pose, get_yaw, rotate_pose,
                    collect_angles, topic3D,
                    topicFeedback, topic2D, get_pose_name)
import tensorflow_hub as hub

keypoints_name = 'human4d_32'
ground_truth_angle = 90

app = Flask(__name__)

users = {}


def calculate_score(processed_image, category):
    """
    Calculate pose score with additional info

    Params:
        processed_img: the output of processed_img
        category: pose category

    Returns:
        the calculated score with additional info
        {
        "score": <score>,
        "angles": <angles>
        }
    """
    # TODO: Stuff goes here later
    angles = processed_image.get("angles")
    print('angles', angles)
    print('angles type', type(angles))
    pose_name = get_pose_name(category)
    evaluation = evaluate_pose(angles, pose_name)

    return json.dumps({
            "score": evaluation,
            "angles": angles,
            })


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")


def publish_results(deviceid, userid, pose3D, score, pose2D, category):
    """
    Publish the calculated results to a MQTT server

    Params:
     deviceid: ID of the device as a str
     userid: ID of the user as a str
     pose3D: published under the /pose3D topic
     score: published  under the /feedback topic
     movenet: published under the /pose2D topic
     category: published under the /feedback topic

    Returns:
     Nothing
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_publish = print("message sent!")
    client.connect("mqtt.eclipseprojects.io", 1883, 60)

    client.loop_start()
    topic3d = topic3D(userid, deviceid)
    print("publishing 3D Pose")
    client.publish(topic=topic3d, payload=pose3D, qos=1)
    print("3D pose published on", topic3d)

    topic2d = topic2D(userid, deviceid)
    print("publishing 2D Pose")
    client.publish(topic=topic2d, payload=pose2D, qos=1)
    print("2D pose published on", topic2d)

    topicfeedback = topicFeedback(userid, deviceid)
    print("publishing feedback on", topicfeedback)
    client.publish(topic=topicfeedback, payload=score, qos=1)
    print("feedback published")
    client.loop_stop()


def process_img(img):
    """
    Processes the image and returns the 3D poses plus the angles
    in a json object

    Params:
        img: the image array

    Returns:
        json object of format
        {
            "pose3D": [<pose>],
            "angles": [<angle1>, <angle2>, <angleN>],
        }
    """
    pred = model.detect_poses(img, skeleton=keypoints_name)
    yaw = get_yaw(pred['poses3d'])
    rotated = rotate_pose(pred['poses3d'], 0)
    angles = collect_angles(rotated)
    result = {
            "pose3D": rotated,
            "angles": angles
            }
    return result

def get_pose3d(processed_img):
    return json.dumps({
        "pose3D": processed_img.get("pose3D").tolist()
        })

def get_pose2d(pose2D):
    return json.dumps({
        "pose2D": pose2D
        })


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
    """
    Recives data to publish under the MQTT server
    """
    json_body_request = request.get_json()
    data = json_body_request.get("data")
    user = json_body_request.get("user")
    device = str(json_body_request.get("device"))
    shape = eval(json_body_request.get("shape"))
    pose2D = json_body_request.get("movenet")
    category = eval(json_body_request.get("category"))
    print("category:", category)
    print("category data type:", type(category))

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
    user = str(user)[2:-1]
    fernet = Fernet(base64.b64encode(secret[:32].encode()))
    decrypted_data = fernet.decrypt(data[2:-1].encode())
    decompressed = gzip.decompress(decrypted_data)
    array = np.reshape(np.frombuffer(decompressed, dtype=np.uint8), shape)

    processed_img = process_img(array)
    pose3D = get_pose3d(processed_img)
    pose2D = get_pose2d(pose2D)
    score = calculate_score(processed_img, category)
    publish_results(device, user, pose3D, score, pose2D, category)
    return "Hi"


if __name__ == '__main__':
    print("""
    This file meant to run on the VPS/Server to recive data from other clients
    process them, and publish them under the specified topics
    """)
    model = hub.load('./venv/models/metrabs_s_256/')  # Takes about 5 minutes
    d1 = DiffieHellman()
    pubkey = d1.gen_public_key()
    app.run(debug=False, port=8080, host='0.0.0.0')
