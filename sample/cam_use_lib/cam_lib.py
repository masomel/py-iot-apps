from subprocess import call

def_cmd = 'raspistill -t 500 -w 1024 -h 768 -o /tmp/test.jpg'

def take_pic(name):
    cmd = 'raspistill -t 500 -w 1024 -h 768 -o ' + name
    call([cmd], shell=True)


def take_pic_def():
    call([def_cmd], shell=True)
