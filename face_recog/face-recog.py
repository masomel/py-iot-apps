"""Raspberry Pi Face Recognition Treasure Box
Treasure Box Script
Copyright 2013 Tony DiCola
"""
import tracer

import cv2

from opencv import config
from opencv import face

def detect_face():
        # Load training data into model
        print('Loading training data...')
        model = cv2.createEigenFaceRecognizer()
        model.load(config.TRAINING_FILE)
        print('Training data loaded!')
        # Initialize camera
        camera = config.get_camera()
        print('Running...')

        # Check for the positive face and unlock if found.
        image = camera.read()
        # Convert image to grayscale.
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        # Get coordinates of single face in captured image.
        result = face.detect_single(image)
        if result is None:
                print('Could not detect single face!  Check the image in' \
                      ' capture.pgm to see what was captured and try' \
                      'again with only one face visible.')
        else:
                x, y, w, h = result
                # Crop and resize image to face.
                crop = face.resize(face.crop(image, x, y, w, h))
                # Test face against model.
                label, confidence = model.predict(crop)
                print('Predicted %s face with confidence %s (lower ' \
                      'is more confident).' %
                      ('POSITIVE' if label == config.MARS_LABEL else
                       'NEGATIVE', str(confidence)))
                if label == config.MARS_LABEL and confidence < config.POSITIVE_THRESHOLD:
                        print('Hello mars')
                else:
                        print('Did not recognize face!')

tracer.start_tracer(detect_face)

