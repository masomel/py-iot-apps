echo "Recording your Speech (Ctrl+C to Transcribe)"
arecord -D plughw:0,0 -q -f cd -t wav -d 4 -r 16000 | flac - -f --best --sample-rate 16000 -s -o talkingganesha.flac;