import tensorflow as tf
import tensorflow_hub as hub
import numpy as np

import enum
"""
This file is meant to test the movenet and pose classifier on the raspberry pi
"""


class BodyPart(enum.Enum):
    """
    Enum representing human body keypoints detected by pose estimation models.
    """
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16

def load_movenet(path):
    """
    Loads the movenet model from local files

    Params:
        path: path to the movenet model (directory)

    Returns:
        the movenet model
    """
    model = hub.load(path)
    movenet = model.signatures['serving_default']
    return movenet


def use_movenet(img, movenet):
    """
    Uses the movenet model to make pose estimation

    Params:
        img: the input image
        movenet: the movenet model (output of load_movenet)

    Returns:
        estimated pose
    """
    input_size = 256
    image = tf.expand_dims(img, axis=0)
    image = tf.image.resize_with_pad(image, input_size, input_size)
    image = tf.cast(image, dtype=tf.int32)

    outputs = movenet(image)
    # Output is a [1, 1, 17, 3] tensor.
    keypoints_with_scores = outputs['output_0'].numpy()
    print("keypoints_with_scores: ", keypoints_with_scores)
    return keypoints_with_scores


def person_from_keypoint(keypoints_with_scores, image_width, image_height):
    """
    Converts the output to a reasonable [[x, y, score]] where the x and y
    represent a keypoint in an image
    Args:
        keypoints_with_scores: output of `movenet`
        image_width: image width
        image_height: image_height
    Returns:
        tensor of shape (1, 17, 3) with the x, y and confident score
    """
    keypoints_with_scores = tf.reshape(keypoints_with_scores, (17, 3))
    kpts_x = keypoints_with_scores[:, 1]
    kpts_y = keypoints_with_scores[:, 0]
    scores = keypoints_with_scores[:, 2]
    # Convert keypoints to the input image coordinate system.
    keypoints = []
    for i in range(scores.shape[0]):
        keypoints.append(
            [int(kpts_x[i] * image_width),
                int(kpts_y[i] * image_height),
                scores[i]])
    return tf.convert_to_tensor(keypoints)


def extract_keypoints(keypoints_with_scores):
    """
    extract the x and y of person's keypoint from an image
    Args:
        keypoints_with_scores: keypoints with score
    """
    keypoints = person_from_keypoint(keypoints_with_scores, 256, 256)
    # movenet = Movenet('movenet_thunder')
    # keypoints = movenet.detect(np.array(input_image))
    # the 0th index of the `keypoints` array contains the indexes of
    # each body part in
    toreturn = []
    for keypoint in keypoints:
        toreturn.append(keypoint[0])
        toreturn.append(keypoint[1])
    return tf.convert_to_tensor([toreturn]).numpy().astype(np.float32)


def get_center_point(landmarks, left_bodypart, right_bodypart):
    """Calculates the center point of the two given landmarks."""
    left = tf.gather(landmarks, left_bodypart.value, axis=1)
    right = tf.gather(landmarks, right_bodypart.value, axis=1)
    center = left * 0.5 + right * 0.5
    return center


def get_pose_size(landmarks, torso_size_multiplier=2.5):
    """Calculates pose size.

    It is the maximum of two values:
    * Torso size multiplied by `torso_size_multiplier`
    * Maximum distance from pose center to any pose landmark
    """
    # Hips center
    hips_center = get_center_point(landmarks, BodyPart.LEFT_HIP,
                                   BodyPart.RIGHT_HIP)

    # Shoulders center
    shoulders_center = get_center_point(landmarks, BodyPart.LEFT_SHOULDER,
                                        BodyPart.RIGHT_SHOULDER)

    # Torso size as the minimum body size
    torso_size = tf.linalg.norm(shoulders_center - hips_center)
    # Pose center
    pose_center_new = get_center_point(landmarks, BodyPart.LEFT_HIP,
                                       BodyPart.RIGHT_HIP)

    pose_center_new = tf.expand_dims(pose_center_new, axis=1)
    # Broadcast the pose center to the same size as the landmark vector to
    # perform substraction
    pose_center_new = tf.broadcast_to(pose_center_new,
                                      [tf.size(landmarks) // (17*2), 17, 2])

    # Dist to pose center
    d = tf.gather(landmarks - pose_center_new, 0, axis=0,
                  name="dist_to_pose_center")
    # print('the d: ', d)
    # Max dist to pose center
    max_dist = tf.reduce_max(tf.linalg.norm(d, axis=0))

    # Normalize scale
    pose_size = tf.maximum(torso_size * torso_size_multiplier, max_dist)
    return pose_size


def normalize_pose_landmarks(landmarks):
    """
    Normalizes the landmarks translation by moving the pose center to (0,0) and
    scaling it to a constant pose size.
    """
    # Move landmarks so that the pose center becomes (0,0)
    pose_center = get_center_point(landmarks, BodyPart.LEFT_HIP,
                                   BodyPart.RIGHT_HIP)

    pose_center = tf.expand_dims(pose_center, axis=1)
    # Broadcast the pose center to the same size as the landmark vector to
    # perform substraction
    pose_center = tf.broadcast_to(pose_center,
                                  [tf.size(landmarks) // (17*2), 17, 2])
    landmarks = landmarks - pose_center

    # Scale the landmarks to a constant pose size
    pose_size = get_pose_size(landmarks)
    landmarks /= pose_size
    return landmarks


def preprocess(keypoints):
    """
    proprocessing
    """
    points = tf.reshape(keypoints, (1, 17, 2))
    new_points = normalize_pose_landmarks(points)
    return tf.keras.layers.Flatten()(new_points)


def classify(points, classifier):
    """
    Classify a pose to one of eight pre-defined poses using the classifier

    Params:
        points: outout of the movenet model
        classifier: the keras classifer

    Returns:
        classified result
    """
    toreturn = classifier.predict(points)
    return toreturn

def load_classifier(path):
    """
    Loads the classifier model from local files

    Params:
        path: path to the classifier model (to the .keras file)

    Returns:
        the classifier
    """
    return tf.keras.models.load_model('./venv/models/classifier/model.keras')

def use_classifier(keypoints_with_scores, classifier):
    # person_from_keypoint(keypoints_with_scores, 256, 256)
    keypoints = extract_keypoints(keypoints_with_scores)
    preprocesed = preprocess(keypoints)
    print("using classifier")
    return classify(preprocesed, classifier)
