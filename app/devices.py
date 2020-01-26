class Device(object):
    devices = []

    def __init__(self, pin, status):
        self.pin = pin
        self.status = status
