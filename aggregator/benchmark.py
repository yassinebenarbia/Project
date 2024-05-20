from movenet import (use_movenet, use_classifier, load_movenet, load_classifier)
import tensorflow as tf
def my_func():
    model = load_movenet("./venv/models/movenet/thunder/")
    classifier = load_classifier("./venv/models/classifier/model.keras")

    images = ['1.jpeg', '2.jpeg', '3.jpeg', '4.jpeg']
    # images = ['1.jpeg']
    for image in images:
        image_path = 'venv/data/'+image
        image = tf.io.read_file(image_path)
        image = tf.image.decode_jpeg(image)
        result = use_movenet(image, model)
        use_classifier(result, classifier)

if __name__ == '__main__':
    my_func()
