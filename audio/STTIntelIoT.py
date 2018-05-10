# msm: source - http://www.instructables.com/id/Speech-to-Text/?ALLSTEPS

import speech_recognition as sr

r = sr.Recognizer()

with sr.WavFile("test.wav") as source: # use "test.wav" as the audio source
    r.energy_threshold = 4000
    audio = r.record(source) # extract audio data from the file

try:

    print(("You said " + r.recognize(audio))) # recognize speech using Google Speech Recognition except IndexError: # the API key didn't work

    print("No internet connection")

except KeyError: # the API key didn't work

    print("Invalid API key or quota maxed out")

except LookupError: # speech is unintelligible

    print("Could not understand audio")
