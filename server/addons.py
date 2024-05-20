from enum import Enum
import numpy as np
import json
import math
import paho.mqtt.client as mqtt
from math import exp
from numpy import interp


def yaw_angle(direction):
    """
    Calculates the yaw angle of a 3D line in radians.

    Args:
      direction: A numpy array of shape (3,) representing the direction vector
      of the line.

    Returns:
      The yaw angle of the line in radians.
    """
    # project the direction vector onto the XZ plane
    projected_direction = np.array([direction[0], 0.0, direction[2]])

    # calculate yaw angle and convert it to degrees
    yaw = np.arctan2(projected_direction[0], projected_direction[2])
    yaw = np.degrees(yaw)
    return yaw

def get_yaw(pose):
    """
    Gets the yaw angle ofa 3D pose of `humand4d_32` keypoints index

    Args:
      pose: numpy array of shape (1, 32, 3)

    Returns:
      Yaw angle in degrees
    """

    start_point = pose[0][20]
    end_point = pose[0][26]

    # Calculate the direction vector
    direction = end_point - start_point

    # Calculate the yaw angle
    yaw = yaw_angle(direction)
    return yaw

def create_yaw_rotation_matrix(yaw_angle_radians):
    c, s = np.cos(yaw_angle_radians), np.sin(yaw_angle_radians)
    return np.array([[c, -s, 0],
                     [s, c, 0],
                     [0,  0, 1]])

def rotate_pose(points, yaw_angle_degrees):
  yaw_angle_radians = np.deg2rad(yaw_angle_degrees)
  rotation_matrix = create_yaw_rotation_matrix(yaw_angle_radians)
  res = []
  for point in points[0]:
    temp_point = [point[0], point[2], point[1]]
    rotated_point = rotate_points(temp_point, rotation_matrix)[0]
    res.append([rotated_point[0], rotated_point[2], rotated_point[1]])
  return np.array([res])

def rotate_points(points, rotation_matrix):
    points = np.atleast_2d(points)
    rotated_points = np.dot(points, rotation_matrix.T)
    return rotated_points


def publish_processed(process, topic="/number/process"):
    pass


def publish_pose(pose, topic="/number/body/"):
  client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
  client.connect("mqtt.eclipseprojects.io", 1883, 60)
  client.on_connect = print("connected!")
  client.on_publish = print("message sent!")

  client.loop_start()
  client.publish(topic=topic, payload=pose, qos=2)
  client.loop_stop()

def extract_angle(a, b, c):
    # Calculate vectors
    ba = a - b
    bc = c - b

    # Calculate dot product
    dot_product = np.dot(ba, bc)

    # Calculate magnitudes
    magnitude_ba = np.linalg.norm(ba)
    magnitude_bc = np.linalg.norm(bc)

    # Calculate cosine of the angle
    cosine_angle = dot_product / (magnitude_ba * magnitude_bc)

    # Calculate angle in radians
    angle_radians = np.arccos(cosine_angle)

    # Convert angle to degrees
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees

from enum import Enum

class HUMAN4D32(Enum):
    PELV = 0
    SPIN0 = 1
    SPIN1 = 2
    SPIN2 = 3
    SPIN3 = 4
    NECK = 5
    NECK2 = 6
    HEAD = 7
    HTOP = 8
    NECK3 = 9
    RSHO = 10
    RELB = 11
    RWRI = 12
    RPINKIE = 13
    RTHU = 14
    LSHO = 15
    LELB = 16
    LWRI = 17
    LPINKIE = 18
    LTHU = 19
    RHIP = 20
    RKNE = 21
    RANK = 22
    RFOO = 23
    RTOE = 24
    RTOE2 = 25
    LHIP = 26
    LKNE = 27
    LANK = 28
    LFEE = 29
    LTOE = 30
    LTOE2 = 31


def collect_angles(poses):
    for pose in poses:
        lelb_angle = extract_angle(pose[HUMAN4D32.LSHO.value],
                                   pose[HUMAN4D32.LELB.value],
                                   pose[HUMAN4D32.LWRI.value])
        relb_angle = extract_angle(pose[HUMAN4D32.RSHO.value],
                                   pose[HUMAN4D32.RELB.value],
                                   pose[HUMAN4D32.RWRI.value])

        rknee_angle = extract_angle(pose[HUMAN4D32.RHIP.value],
                                    pose[HUMAN4D32.RKNE.value],
                                    pose[HUMAN4D32.RANK.value])
        lknee_angle = extract_angle(pose[HUMAN4D32.LHIP.value],
                                    pose[HUMAN4D32.LKNE.value],
                                    pose[HUMAN4D32.LANK.value])

        lhip_angle = extract_angle(pose[HUMAN4D32.LKNE.value],
                                    pose[HUMAN4D32.LHIP.value],
                                    pose[HUMAN4D32.RHIP.value])
        rhip_angle = extract_angle(pose[HUMAN4D32.RKNE.value],
                                    pose[HUMAN4D32.RHIP.value],
                                    pose[HUMAN4D32.LHIP.value])

        hip_angle = extract_angle(pose[HUMAN4D32.LKNE.value],
                                    pose[HUMAN4D32.PELV.value],
                                    pose[HUMAN4D32.RKNE.value])

        lshou_vangle = extract_angle(pose[HUMAN4D32.LELB.value],
                                    pose[HUMAN4D32.LSHO.value],
                                    pose[HUMAN4D32.SPIN0.value])
        lshou_hangle = extract_angle(pose[HUMAN4D32.LELB.value],
                                    pose[HUMAN4D32.LSHO.value],
                                    pose[HUMAN4D32.NECK.value])
        rshou_vangle = extract_angle(pose[HUMAN4D32.RELB.value],
                                    pose[HUMAN4D32.RSHO.value],
                                    pose[HUMAN4D32.SPIN0.value])
        rshou_hangle = extract_angle(pose[HUMAN4D32.RELB.value],
                                    pose[HUMAN4D32.RSHO.value],
                                    pose[HUMAN4D32.NECK.value])

    return json.dumps({
      "lelb": round(lelb_angle),
      "relb": round(relb_angle),
      "lknee": round(lknee_angle),
      "rknee": round(rknee_angle),
      "lhip": round(lhip_angle),
      "rhip": round(rhip_angle),
      "spread": round(hip_angle),
      "hlshoulder": round(lshou_vangle),
      "hrshoulder": round(lshou_hangle),
      "vlshoulder": round(rshou_vangle),
      "vrshoulder": round(rshou_hangle),
    })


# def evaluate_pose(pose_name, pose_angles):
#     """
#     This evaluates a posture based on the extracted angles from the `collect_angles` function
#     and outputs a score that represents how 'good' the attempt is.
#
#     Args:
#     pose_name: position name
#     pose_angles: json object that represent position angles (output of `collect_angles`)
#
#     Returns:
#     Score representative of how 'good' the attempt is that ranges between 0 and 1
#
#     """
#
#     match pose_name:
#         case "dog":
#             print("dog")
#
#         case "warrior":
#             print("warrior")
#
#         case "tree":
#             print("tree")
#
#         case "triangle":
#             print("triangle")
#
#         case "cobra":
#             print("cobra")
#
#         case "chaire":
#             print("chaire")
#
#         case "shoulder-stand":
#             print("shoulder- stand")
#
#         case "tree":
#             print("tree")
#
#         case other:
#             print("nothing")

def topic2D(clientid: str, deviceid: str):
    """
    Generates the 2D pose topic for the given credentials

    Params:
        clientid: the given client id as a str
        deviceid: the given device id as a str

    Returns:
        the needed topic as a string
    """
    return "/"+clientid+"/"+deviceid+"/pose2D"


def topic3D(clientid: str, deviceid: str):
    """
    Generates the 3D pose topic for the given credentials

    Params:
        clientid: the given client id as a str
        deviceid: the given device id as a str

    Returns:
        the needed topic as a string
    """
    return "/"+clientid+"/"+deviceid+"/pose3D"

def topicFeedback(clientid: str, deviceid: str):
    """
    Generates the feedback topic for the given credentials

    Params:
        clientid: the given client id as a str
        deviceid: the given device id as a str

    Returns:
        the needed topic as a string
    """
    return "/"+clientid+"/"+deviceid+"/feedback"


# each coefficient for angle of each pose represnt how importent the angle
# is for the pose, each one should range between 2 and 0 where 2 holds
# the most significant angle and 0 the least significant angle
coefficients = {
    "Dog": {
        "lelb": 0.75,
        "relb": 0.75,
        "lknee": 1.5,
        "rknee": 1.5,
        "lhip": 0.25,
        "rhip": 0.25,
        "spread_ang": 0.5,
        "hlshoulder": 1.5,
        "hrshoulder": 1.5,
        "vlshoulder": 1.5,
        "vrshoulder": 1.5,
    },
     "Cobra": {
        "lelb": 1.5,
        "relb": 1.5,
        "lknee": 0.5,
        "rknee": 0.5,
        "lhip": 0.25,
        "rhip": 0.25,
        "spread_ang": 0.5,
        "hlshoulder": 1.5,
        "hrshoulder": 1.5,
        "vlshoulder": 1.5,
        "vrshoulder": 1.5,
    },
     "Chaire": {
        "lelb": 0.25,
        "relb": 0.25,
        "lknee": 2,
        "rknee": 2,
        "lhip": 1.5,
        "rhip": 1.5,
        "spread_ang": 1.5,
        "hlshoulder": 0.25,
        "hrshoulder": 0.25,
        "vlshoulder": 0.75,
        "vrshoulder": 0.75,
    },
     "SStand": {
        "lelb": 1.25,
        "relb": 1.25,
        "lknee": 0.5,
        "rknee": 0.5,
        "lhip": 0.5,
        "rhip": 0.5,
        "spread_ang": 0.5,
        "hlshoulder": 1.25,
        "hrshoulder": 1.25,
        "vlshoulder": 1.75,
        "vrshoulder": 1.75,
    },
     "Tree": {
        "lelb": 0.25,
        "relb": 0.25,
        "lknee": 1.75,
        "rknee": 1.75,
        "lhip": 1.75,
        "rhip": 1.75,
        "spread_ang": 1.5,
        "hlshoulder": 0.75,
        "hrshoulder": 0.75,
        "vlshoulder": 0.25,
        "vrshoulder": 0.25,
    },
     "Triangle": {
        "lelb": 0.5,
        "relb": 0.5,
        "lknee": 2,
        "rknee": 2,
        "lhip": 1.5,
        "rhip": 1.5,
        "spread_ang": 1.0,
        "hlshoulder": 0.5,
        "hrshoulder": 0.5,
        "vlshoulder": 0.5,
        "vrshoulder": 0.5,
    },
     "Warrior": {
        "lelb": 1.0,
        "relb": 1.0,
        "lknee": 1.75,
        "rknee": 1.75,
        "lhip": 1.5,
        "rhip": 1.5,
        "spread_ang": 1.5,
        "hlshoulder": 0.5,
        "hrshoulder": 0.5,
        "vlshoulder": 0.5,
        "vrshoulder": 0.5,
    },
}


def angle_difference(angle1, angle2):
    return min(abs(angle1 - angle2), 360 - abs(angle1 - angle2))


def calculate_diffs(pose_name, pose_angles):
    diffs = {}
    print("Pose angles:", pose_angles)
    print("Pose angles type:", type(pose_angles))
    pose_angles = json.loads(pose_angles)
    with open("venv/json/"+pose_name+".json") as truth:
        o = json.load(truth)

        diffs["lelb"] = angle_difference(o.get("lelb"), pose_angles.get("lelb"))
        diffs["relb"] = angle_difference(o.get("relb"), pose_angles.get("relb"))
        diffs["lknee"] = angle_difference(o.get("lknee"), pose_angles.get("lknee"))
        diffs["rknee"] = angle_difference(o.get("rknee"), pose_angles.get("rknee"))
        diffs["lhip"] = angle_difference(o.get("lhip"), pose_angles.get("lhip"))
        diffs["rhip"] = angle_difference(o.get("rhip"), pose_angles.get("rhip"))
        diffs["spread_ang"] = angle_difference(o.get("spread_ang"),
                                               pose_angles.get("spread"))
        diffs["hlshoulder"] = angle_difference(o.get("hlshoulder"),
                                               pose_angles.get("hlshoulder"))
        diffs["hrshoulder"] = angle_difference(o.get("hrshoulder"),
                                               pose_angles.get("hrshoulder"))
        diffs["vlshoulder"] = angle_difference(o.get("vlshoulder"),
                                               pose_angles.get("vlshoulder"))
        diffs["vrshoulder"] = angle_difference(o.get("vrshoulder"),
                                               pose_angles.get("vrshoulder"))
        return diffs


def map_coef(pose_name, key):
    """
    Returns:
      value between 0 and 1
    """
    thing = coefficients.get(pose_name)
    coef = thing.get(key)
    high = max(thing.values())
    return coef / high


def calculate_score(diff):
    """
    Calculates the score given the angle difference for a particular
    pose

    Args:
      diff: output of the calculate_diffs funciton

    Returns:
       reanges a score between [1 and 0], 1 means good and 0 means bad

    """
    v = min(diff, 45)
    if v < 5:
        return interp(v, [0, 5], [1, 0.90])
    elif v < 10:
        return interp(v, [5, 10], [0.90, 0.80])
    elif v < 15:
        return interp(v, [10, 15], [0.80, 0.70])
    elif v < 20:
        return interp(v, [15, 20], [0.70, 0.50])
    elif v < 25:
        return interp(v, [20, 25], [0.50, 0.40])
    else:
        return interp(v, [25, 45], [0.40, 0.0])


def evaluate_diffs(pose_name, diffs):
    evaluated = []
    for key, value in diffs.items():
        evaluated.append(calculate_score(value) *
                         coefficients.get(pose_name).get(key))
    print(evaluated)
    return (sum(evaluated) / 11)


def evaluate_pose(pose_angles, pose_name):
    """
    This evaluates a posture based on the extracted angles from the
    `collect_angles` function and outputs a score that represents how
    'good' the attempt is.

    Args:
        pose_name: position name
        pose_angles: json object that represent position
                    angles (output of `collect_angles`)

    Returns:
        Score representative of how 'good' the position is, this score
        that ranges between 0 and 1
    """
    print("pose name:", pose_name)
    if pose_name == "NoPose" or pose_name is None:
        return 0.0
    diffs = calculate_diffs(pose_name, pose_angles)
    return evaluate_diffs(pose_name, diffs)


def get_pose_name(arr):
    """
    returns the pose name

    Args:
        arr: array represent the classifier output
            (got from the request 'category')
    """

    print(arr)
    max_index = max(enumerate(arr[0]), key=lambda x: x[1])[0]
    print("max index:", max_index)
    match max_index:
        case 0:
            return "Chair"
        case 1:
            return "Cobra"
        case 2:
            return "Dog"
        case 4:
            return "Traingle"
        case 5:
            return "SStand"
        case 6:
            return "Tree"
        case 7:
            return "Warrior"
        case other:
            return "NoPose"
