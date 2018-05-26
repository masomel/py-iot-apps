import io
import os

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

# Instantiates a client
client = speech.SpeechClient()

# The name of the audio file to transcribe
file_name = os.path.join(
            os.path.dirname(__file__),
            'resources',
            'good-morning-google-mono.flac')
print(file_name)
print(type(file_name))
print(enums)
print(type(enums))
print(enums.RecognitionConfig.AudioEncoding)
print(type(enums.RecognitionConfig.AudioEncoding))

# Loads the audio into memory
with io.open(file_name, 'rb') as audio_file:
    content = audio_file.read()
    audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
         encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
         sample_rate_hertz=44100,
         language_code='en-US')

    # Detects speech in the audio file
    response = client.recognize(config, audio)

    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))