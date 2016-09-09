import tracer

def hello():
    print("Hello, world")

tracer.start_tracer(hello)
