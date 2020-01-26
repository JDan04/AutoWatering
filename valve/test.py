import json

with open("data.json", "r") as json_file: # Opens .json file
    data = json.load(json_file) # Loads contents of .json into a python dictionary

for key, value in data["devices"].items():
    print(str(key) + " " + str(value))
