 # Imports needed libraries
import paho.mqtt.client as mqtt
from datetime import datetime
import RPi.GPIO as GPIO
import time
import json
import sys
import os

# Imports classes from other files
from devices import Device

try:
    fail_con_startup = 1 # Initializes used variables

    found = False

    global init_time
    init_time = 0

    path = "/home/pi/"

    global if_disconnected
    if_disconnected = False # Creates bool state

    GPIO.setmode(GPIO.BCM)

    with open("data.json", "r") as json_file: # Opens .json file
        data = json.load(json_file) # Loads contents of .json into a python dictionary

    broker = data["data"]["broker"][0]

    sub_topic = data["data"]["topic"]["sub"]
    pub_topic = data["data"]["topic"]["pub"]

    # Initialize devices and creates a list of valves
    valves = []
    for key, value in data["devices"].items():
        if data["devices"][key]["type"] == "valve":
            valves.append(key)
            globals()[key] = Device(int(data["devices"][key]["pin"]), "Off")
            GPIO.setup(globals()[key].pin, GPIO.OUT, initial=GPIO.HIGH)

    sws_led = Device(25, "Off")
    GPIO.setup(sws_led.pin, GPIO.OUT, initial=GPIO.HIGH)

    # Create files for recording time
    def create_files():
        for i in valves:
            t = open(i + "_time.txt", "w") # Here was the stop
            t.write(str(datetime.now())[5:10] + ' {}'.format(init_time))
            t.close()

    def record_time(device):
        try:
            r = open(device + "_time.txt", "r").readlines()
            new_time = round((float(str(r[-1]).split()[1]) + ((time.time() - globals()[device + "_time_start"]) / 60)), 2)
            globals()[device + "_time_start"] = time.time()
            r.append(str(datetime.now())[5:10] + ' {}'.format(new_time))
            del r[-2]
            os.remove(device + "_time.txt")
            with open(device + "_time.txt", "w") as t:
                for i in r:
                     t.write(i)
                t.close()
        except:
            print("Either an Error ocurred when recording time, or the valves were never activated today.")
            pass

    def valve_open(pin): # Called when requesting opening of valve
        GPIO.output(pin, GPIO.LOW) # Switching relay "on"

    def valve_close(pin): # Called when requesting closing of valve
        GPIO.output(pin, GPIO.HIGH) # Switching relay "off"

    def on_connect(client, userdata, flags, rc): # Runs when connected to MQTT broker
        if rc == 0:
            if if_disconnected:
                print("Reconnection succesfull")

                client.subscribe(sub_topic) # Subscribes to topic "well/action"
                client.publish(pub_topic, "Well_Zero - " + str(datetime.now()).split(".")[0] + "\nReconnection to " + broker + " succesfull!") # Publishes when initialization complete to "well/log"
            else:
                print("Connection succesfull with status OK")

                client.subscribe(sub_topic) # Subscribes to topic "well/action"
                client.publish(pub_topic, "Well_Zero - " + str(datetime.now()).split(".")[0] + "\nConnection to " + broker + " succesfull!") # Publishes when initialization complete to "well/log"
        else:
            print("Bad connection. Returned code: ", rc) # Prints when connection unsuccesfull

    def on_log(client, userdata, lever, buf): # Logs to console
        print("log: " + buf)

    def on_message(client, userdata, msg): # Runs when message recieved
        try:
            topic = msg.topic
            print("Message received:", str(msg.payload.decode("utf-8")).capitalize()) # Prints recieved message to console
            m_decode = str(msg.payload.decode("utf-8")).lower().split() # Converts msg to a string + makes it lower case

            global devices

            global valve1_time_start
            global valve2_time_start

            for i in valves:
                if m_decode[1] == i:
                    if m_decode[0] == "open" and globals()[i].status == "Off":
                        valve_open(globals()[i].pin)
                        globals()[i].status = "On"
                        print(str(i + " has been opened").capitalize())
                        client.publish(pub_topic, "Well_Zero - " + str(datetime.now()).split(".")[0] + "\n" + str(i + " has been opened").capitalize())
                        globals()[i + "_time_start"] = time.time()
                    if m_decode[0] == "close" and globals()[i].status == "On":
                        valve_close(globals()[i].pin)
                        globals()[i].status = "Off"
                        print(str(i + " has been closed").capitalize())
                        client.publish(pub_topic, "Well_Zero - " + str(datetime.now()).split(".")[0] + "\n" + str(i + " has been closed").capitalize())
                        record_time(i)

                    if m_decode[0] == "request":
                        if m_decode[1] == i and globals()[i].status == "On":
                            record_time(i)

                        with open(i + "_time.txt", "r") as r:
                            client.publish(pub_topic, str(i + " " + globals()[i].status + " " + r.readlines()[-1].split()[1]))
                            r.close()

        except IndexError:
            pass

    def on_disconnect(client, userdata, flags, rc=0): # Runs on disconnect from MQTT broker
        # Creates a .txt file "fail_log.txt"
        fail_log = open(str(datetime.now()).split(".")[0].replace(":", "-")[:10] + " - fail_log.txt", "a+")
        fail_log.write(str(datetime.now()) + " - Unexpected disconnect with result code " + str(rc) + "\n")
        fail_log.close()

        print("Unexpected disconnect with result code " + str(rc) + ". Attempting auto-reconnect.")

        # Closes both valves on disconnect
        for i in valves:
            if globals()[i].status == "On":
                GPIO.output(globals()[i].pin, GPIO.HIGH)
                globals()[i].status = "Off"
                record_time(i)

        if_disconnected = True # Sets if_disconnected to True for change in on_connect logback

    client = mqtt.Client("well_zero") # Sets up MQTT client

    # Sets up callbacks
    client.on_connect = on_connect
    # client.on_log = on_log
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print("Connecting to broker", broker)

    while True:
        try:
            print("- Attempt #" + str(fail_con_startup))
            client.connect(broker) # Attempts to connect to MQTT broker
            break
        except OSError: # If connection to broker fails
            if fail_con_startup >= 5: # If there were five connection attempts
                print("Unable to connect to the broker. Trying again in approx. 15 minutes.")

                fail_log = open(str(datetime.now()).split(".")[0].replace(":", "-")[:10] + " - fail_log.txt", "a+")
                fail_log.write(str(datetime.now()) + " - Unable to connect to the broker. Trying again in approx. 15 minutes.\n")
                fail_log.close()

                # Closes both valves on disconnect
                for i in valves:
                    GPIO.output(globals()[i].pin, GPIO.HIGH)
                    globals()[i].status = "Off"
                    record_time(i)

                GPIO.cleanup() # Cleans GPIO pins
                sys.exit() # Exits program cleanly
            else:
                print("Attempt failed. Trying again in 10 seconds.")
                fail_con_startup += 1 # += 1 to attempts
                time.sleep(10) # Waits ten seconds
                pass

    for f in os.listdir(path):
        for i in valves:
            if f == str(i + "_time.txt"):
                found = True
                break

    if not found:
        create_files()

    client.loop_start() # Starts MQTT loop

    while True:
        try:
            for i in valves:
                with open(i + "_time.txt", "r") as r:
                    if str(datetime.now())[5:10] != str(r.readlines()[-1]).split(" ")[0]:
                        with open(i + "_time.txt", "a+") as t:
                            t.write("\n" + str(datetime.now())[5:10] + ' {}'.format(init_time))
                            t.close()
                    else:
                        pass
                    r.close()
        except (FileNotFoundError, IndexError) as error:
            pass

except KeyboardInterrupt: # Runs when KeyboardInterrupt
    GPIO.cleanup() # Cleans GPIO pins
    sys.exit() # Exits program cleanly
