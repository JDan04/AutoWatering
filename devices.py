class Group:
    def __init__(self, name):
        self.name = name

        if name == "active_respondent":
            display_name = "Response Units"
        elif name == "text_respondent":
            display_name = "Text Display"
        else:
            display_name = name

class Device(object):
    devices = []

    def __init__(self, name, display_name, type, pin, status):
        self.name = name
        self.display_name = display_name
        self.type = type
        self.pin = pin
        self.status = status

        self.devices.append(name)