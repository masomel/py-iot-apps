import tracer

def fileio():
    f = open("num.txt", "rw")
    # the first byte of the file contains a number
    num = int(f.read(1))
    f.write(str(num+1))
    f.close()

tracer.start_tracer(fileio)
