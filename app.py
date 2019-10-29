from flask import Flask, render_template, request
from datetime import datetime
import paho.mqtt.client as mqtt
import time
import json
import sys
import os

try:
    broker = "192.168.1.130" # Set broker IP

    global prev_date

    global valve1_saved_time
    valve1_saved_time = 0

    global valve2_saved_time
    valve2_saved_time = 0

    global if_disconnected
    if_disconnected = False # Creates bool state

    global testing_action
    testing_action = False # Creates variable for detecting if web page is just refreshing or if an action is requested

    def on_connect(client, userdata, flags, rc): # Runs when connected to MQTT broker
        if rc == 0:
            if if_disconnected: # Check if connection happening at start or after an unexpected disconnect
                print("Reconnection succesfull")

                client.subscribe("well/request") # Resubscribes to set topic
                client.publish("web/log", "WebApp - " + str(datetime.now()).split(".")[0] + "\nReconnection to " + broker + " succesfull!") # Publishes when reconection complete to "web/log"
            else:
                print("Connection status OK\n") # Prints that connection has been established

                client.subscribe("well/request") # Subscribes to set topic
                client.publish("web/log", "WebApp - " + str(datetime.now()).split(".")[0] + "\nConnection to " + broker + " succesfull!") # Publishes when initialization complete to "web/log"
        else:
            print("Bad connection. Returned code: ", rc + "\n") # Prints when connection unsuccesfull

    def on_log(client, userdata, lever, buf): # Logs to console
        print("log: " + buf)

    def on_message(client, userdata, msg): # Runs when message recieved
        try:
            topic = msg.topic # Gets the topic that the msg came on
            m_decode = str(msg.payload.decode("utf-8")).lower().split() # Converts msg to a string + makes it lower case
            print("Message received: " + str(msg.payload.decode("utf-8"))) # Prints recieved message to console

            # Sets up global variables
            global well_recieved
            global testing_action
            global previous
            global did_change
            global device
            global prev_date

            global valve1_saved_time
            global valve2_saved_time

            # The following segment should be fit for any device with a simple on/off mechanic such as a light etc.

            if not testing_action: # Tests if request was made on refresh or if an action is being assesed
                with open("status.json", "r") as json_file: # Opens .json dictionary
                    status_dict = json.load(json_file) # Loads contets of .json into a python dictionary

                    for controller, devices in status_dict.items(): # Cycles through controllers
                        for device, lst in devices.items(): # Cycles through devices of said controller
                            if device == m_decode[0]: # Runs when affected device maches device in dictionary
                                del status_dict[controller][device] # Deletes the device and it's status from the dictionary

                                if m_decode[1] == "on": # Tests if device was set on
                                    status_dict[controller][device] = ["On", m_decode[2]] # Creates "new" device and status in dictionary
                                if m_decode[1] == "off": # Tests if device was set off
                                    status_dict[controller][device] = ["Off", m_decode[2]] # Creates "new" device and status in dictionary

                                globals()[device + "_saved_time"] = m_decode[2]
                                prev_date = str(datetime.now())[6:10]

                    json_file.close() # Closes .json file

                os.remove("status.json") # Deletes .json file

                with open("status.json", "w") as json_file: # Creates new .json file
                    json.dump(status_dict, json_file) # Dumps updated dictionary to .json
                    json_file.close() # Closes .json file

                well_recieved = True # Sets well_recieved to True to inform that a request response has been recieved

            if testing_action: # Tests if request was made on refresh or if an action is being assesed
                if m_decode[1] == "on" and m_decode[1] != previous: # Finds returned state
                    did_change = True # If change happened sets did_change to True
                if m_decode[1] == "off" and m_decode[1] != previous: # Finds returned state
                    did_change = True # If change happened sets did_change to True

                if did_change:
                    if device == m_decode[0]:
                        globals()[device + "_saved_time"] = m_decode[2]
                        prev_date = str(datetime.now())[6:10]

        except IndexError:
            pass

    def on_disconnect(client, userdata, flags, rc=0): # Runs on disconnect from MQTT broker
        # Creates a .txt file "fail_log.txt"
        fail_log = open(str(datetime.now()).split(".")[0].replace(":", "-")[:10] + " - fail_log.txt", "a+")
        fail_log.write(str(datetime.now()) + " - Unexpected disconnect with result code " + str(rc) + "\n")
        fail_log.close()

        print("Unexpected disconnect with result code " + str(rc) + ". Attempting auto-reconnect.")

        if_disconnected = True

    client = mqtt.Client("webapp") # Sets up MQTT client

    # Sets up callbacks
    client.on_connect = on_connect
    client.on_log = on_log
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print("Connecting to broker", broker)

    fail_con_startup = 1

    while True:
        try:
            print("Attempt " + str(fail_con_startup))
            client.connect(broker) # Attempts to connect to MQTT broker
            print("Connection succesfull")
            break
        except OSError: # If connection to broker fails
            if fail_con_startup >= 5: # If there were five connection attempts
                print("Unable to connect to the broker. Trying again in approx. 15 minutes.")

                # Creates a .txt file "fail_log.txt"
                fail_log = open(str(datetime.now()).split(".")[0].replace(":", "-")[:10] + " - fail_log.txt", "a+")
                fail_log.write(str(datetime.now()) + " - Unable to connect to the broker. Trying again in approx. 15 minutes.\n")
                fail_log.close()

                sys.exit() # Exits program cleanly
            else:
                print("Attempt failed. Trying again in 10 seconds.")
                fail_con_startup += 1 # += 1 to attempts
                time.sleep(10) # Waits ten seconds
                pass

except KeyboardInterrupt: # Runs if program stoped anytime during the setup phase
    sys.exit() # Exits code nicely

try:
    app = Flask(__name__) # Creates flask object

    @app.route("/") # Routes here when url: 192.168.1.xxx:8000/
    def index():
        # Replace following two lines with cycling through devices to get requests !!!!!!!!!!!!!
        client.publish("well/action", "request valve1") # Requests status of valve1
        client.publish("well/action", "request valve2") # Requests status of valve2

        global prev_date

        global valve1_saved_time
        global valve2_saved_time

        # Sets up bool variable to chcek if response from aformentioned request recieved
        global well_recieved
        well_recieved = False

        time.sleep(0.25) # Waits for request to be processed and result recoreded

        if not well_recieved: # Runs when response not recieved
            try:
                if prev_date != str(datetime.now())[6:10]:
                    print(prev_date)
                    valve1_saved_time = 0
                    valve2_saved_time = 0
            except NameError:
                valve1_saved_time = "no_connection"
                valve2_saved_time = "no_connection"

            with open("status.json", "r") as json_file: # Opens .json file
                status_dict = json.load(json_file) # Loads contents of .json into a python dictionary

                for controller, devices in status_dict.items(): # Cycles through dictionary
                    for device, lst in devices.items():
                        del status_dict[controller][device] # Delets every device and status
                        status_dict[controller][device] = ["no_con", globals()[device + "_saved_time"]] # Replaces evry device and status with no_connection

                json_file.close() # Closes .json file

            os.remove("status.json") # Removes .json file

            with open("status.json", "w") as json_file: # Creates new .json file
                json.dump(status_dict, json_file) # Dumps dictionary to .json file
                json_file.close() # Closes .json file

        with open("status.json", "r") as json_file: # Opens .json file
            status_dict = json.load(json_file) # Loads contents of .json into a python dictionary

        print(status_dict)

        return render_template('index.html', **status_dict) # Renders a .html template and passes on aformentioned dictionary

    @app.route("/<actuator>/<action>") # Routes here when url: 192.168.1.xxx:8000/device/action
    def action(actuator, action): # Selects affected device and the controller to contact.
        # Sets up global variables for requesting check after action occurs
        global testing_action
        global previous
        global did_change
        global device
        global prev_date

        with open("status.json", "r") as json_file: # Opens .json file
            status_dict = json.load(json_file) # Loads contents of .json into a python dictionary

            testing_action = True # Changes on_message mode to only check if current status differs from previous status
            did_change = False # Sets up variable to record if current status differs from previous status

            for controller, devices in status_dict.items(): # Cycles through controllers
                for device, info in devices.items(): # Cycles through devices of said controller
                    if device == actuator: # Finds device that maches requestd device
                        if action == "on": # Chceks which action is required
                            previous = "off" # Sets previous state to false
                            state = ["open ", "On"] # Sets up list of action that need to occur
                        if action == "off": # Chceks which action is required
                            previous = "on" # Sets previous state to true
                            state = ["close ", "Off"] # Sets up list of action that need to occur

                        if controller == "well_zero": # Checks which controller the devices are using. May be redundant in the future if commands and topics are same for all devices
                            client.publish("well/action", state[0] + device)
                            client.publish("well/action", "request " + device)

                        time.sleep(0.25) # Waits for requests to be proccesed

                        if did_change: # Checks if the state was change
                            del status_dict[controller][device] # Delets correct device and status in dictionary
                            status_dict[controller][device] = [state[1], str(globals()[device + "_saved_time"])] # Creates new device and status in dictionary

                        if not did_change: # If change in state did not occur
                            if prev_date != str(datetime.now())[6:10]:
                                valve1_saved_time = 0
                                valve2_saved_time = 0

                            del status_dict[controller][device] # Delets correct device and status in dictionary
                            status_dict[controller][device] = ["no_con", str(globals()[device + "_saved_time"])] # Creates new device and status in dictionary

            json_file.close() # Closes .json file

        testing_action = False # Resets on_connect mode

        os.remove("status.json") # Removes .json file

        with open("status.json", "w") as json_file: # Creates new .json file
            json.dump(status_dict, json_file) # Dumps dictionary to .json file
            json_file.close() # Closes .json file

        return render_template('index.html', **status_dict) # Renders a .html template and passes on aformentioned dictionary

    if __name__ == "__main__":
        client.loop_start() # Starts MQTT loop

        app.run(host='0.0.0.0', port=8000, debug=False) # Runs web page

except KeyboardInterrupt: # Runs when program stopped
    client.loop_stop() # Stops MQTT loop
    sys.exit() # Exits program nicely
