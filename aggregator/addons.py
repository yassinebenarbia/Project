from enum import Enum
import numpy as np
import json
import paho.mqtt.client as mqtt


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


def send_processed(process, topic="/number/process"):
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
        "lelb_ang": round(lelb_angle),
        "relb_ang": round(relb_angle),
        "lknee_ang": round(lknee_angle),
        "rkne_ang": round(rknee_angle),
        "lhip_ang": round(lhip_angle),
        "rhip_ang": round(rhip_angle),
        "spread_ang":round(hip_angle),
        "lshou_vang": round(lshou_vangle),
        "lshou_hangle": round(lshou_hangle),
        "rshou_vang": round(rshou_vangle),
        "rshou_hangle": round(rshou_hangle),
    })


def evaluate_pose(pose_name, pose_angles):
  """
  This evaluates a posture based on the extracted angles from the `collect_angles` function
  and outputs a score that represents how 'good' the attempt is.

  Args:
    pose_name: position name
    pose_angles: json object that represent position angles (output of `collect_angles`)

  Returns:
    Score representative of how 'good' the attempt is that ranges between 0 and 1

  """
  match pose_name:
    case "dog":
      print("dog")

    case "worrior":
      print("worrior")

    case "tree":
      print("tree")

    case "triangle":
      print("triangle")

    case "cobra":
      print("cobra")

    case "chaire":
      print("chaire")

    case "shoulder-stand":
      print("shoulder- stand")

    case "tree":
      print("tree")

    case other:
      print("nothing")
