# msm: source - https://www.artik.io/blog/2016/07/building-photo-booth-samsung-artik-10/

import speech_recognition as sr
import subprocess
import cv2
# take a photo
def take_a_picture_and_display():
  cap = cv2.VideoCapture(0)
  ret, frame = cap.read()
  cv2.imwrite("photo.jpg", frame)
  cap.release()
  subprocess.call("fbi -T 2 photo.jpg", shell=True)

# obtain audio from the microphone
r = sr.Recognizer()
while True:
  with sr.Microphone() as source:
    print("Say something to ARTIK!")
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source)

  # recognize speech using Google Speech Recognition
  try:
    string = r.recognize_google(audio)
    print(("You said: " + string))
    if "take a picture" in string:
      take_a_picture_and_display()
  except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
  except sr.RequestError as e:
    print(("Could not request results from Google Speech Recognition service: {0}".format(e)))
