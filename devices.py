class Group:
    def __init__(self, name):
        self.name = name

        if name == "active_respondent":
            display_name = "Response Units"
        elif name == "text_respondent":
            display_name = "Text Display"
        else:
            display_name = name

class Device:
    def __init__(self, display_name, pin, status):
        self.name = name
        self.pin = pin
        self.status = status
