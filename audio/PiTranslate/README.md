PiTranslate
===========

David Conroy
http://www.daveconroy.com

Raspberry Pi Translation Tool

I get many requests from people who are still looking for cheap, easy, and fun project ideas for their Raspberry Pi’s, so I wanted to share this translator project I’ve been working on. With very little effort, we can turn this 35$ mini-computer into a feature rich language translator that not only supports voice recognition and native speaker playback, but also is capable of translation between 60+ languages, FREE! Even if you are not interested in building this exact translational tool, there are still many parts of this tutorial that might be interesting to you (speech recognition, text to speech, Microsoft/Google translation APIs). 

More information can be found here:
http://www.daveconroy.com/turn-raspberry-pi-translator-speech-recognition-playback-60-languages/


## Additional instruction for Pyronia testing
tested with Anaconda3 Python 3.6.4

### Credential for Google Cloud Platform Speech-to-Text Service
Use the credential by setting the `GOOGLE_APPLICATION_CREDENTIALS` env variable

`export GOOGLE_APPLICATION_CREDENTIALS="./gstt-028843c105d1.json"`

### Single Channel FLAC Files
GCP Speech-to-Text still only accepts single channel audio files... If any FLAC files have multiple channels,
convert them to single channel by

`ffmpeg -i stereo.flac -ac 1 mono.flac`



