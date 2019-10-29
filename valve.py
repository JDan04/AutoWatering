 # Import needed libraries
import paho.mqtt.client as mqtt
from datetime import datetime
import RPi.GPIO as GPIO
import time
import sys
import os

try:
    devices = {"valve1": ["Off", 23], "valve2": ["Off", 24]}

	# Sets software status LED pin
    sw_status = 25

    fail_con_startup = 1

    found = False

    global init_time
    init_time = 0

    path = "/home/pi/"

    broker = "192.168.1.130" # Set broker IP

    global if_disconnected
    if_disconnected = False # Creates bool state

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(devices["valve1"][1], GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(devices["valve2"][1], GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(sw_status, GPIO.OUT, initial=GPIO.HIGH)

    def create_files():
        for device, info in devices.items():
            t = open(device + "_time.txt", "w")
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
            print("Error when recording time")
            pass

    def valve_open(pin): # Called when requesting opening of valve
        GPIO.output(pin, GPIO.LOW) # Switching relay "on"

    def valve_close(pin): # Called when requesting closing of valve
        GPIO.output(pin, GPIO.HIGH) # Switching relay "off"

    def on_connect(client, userdata, flags, rc): # Runs when connected to MQTT broker
        if rc == 0:
            if if_disconnected:
                print("Reconnection succesfull")

                client.subscribe("well/action") # Subscribes to topic "well/action"
                client.publish("well/log", "Well_Zero - " + str(datetime.now()).split(".")[0] + "\nReconnection to " + broker + " succesfull!") # Publishes when initialization complete to "well/log"
            else:
                print("Connection status OK")

                client.subscribe("well/action") # Subscribes to topic "well/action"
                client.publish("well/log", "Well_Zero - " + str(datetime.now()).split(".")[0] + "\nConnection to " + broker + " succesfull!") # Publishes when initialization complete to "well/log"
        else:
            print("Bad connection. Returned code: ", rc) # Prints when connection unsuccesfull

    def on_log(client, userdata, lever, buf): # Logs to console
        print("log: " + buf)

    def on_message(client, userdata, msg): # Runs when message recieved
        try:
            topic = msg.topic
            m_decode = str(msg.payload.decode("utf-8")).lower().split() # Converts msg to a string + makes it lower case
            print("Message received:", m_decode) # Prints recieved message to console

            global devices

            global valve1_time_start
            global valve2_time_start

            for device, info in devices.items():
                if m_decode[1] == device:
                    if m_decode[0] == "open" and info[0] == "Off":
                        valve_open(info[1])
                        devices[device] = ["On", info[1]]
                        print(str(device + " has been opened").capitalize())
                        client.publish("well/log", "Well_Zero - " + str(datetime.now()).split(".")[0] + "\n" + str(device + " has been opened").capitalize())
                        globals()[device + "_time_start"] = time.time()
                    if m_decode[0] == "close" and info[0] == "On":
                        valve_close(info[1])
                        devices[device] = ["Off", info[1]]
                        print(str(device + " has been closed").capitalize())
                        client.publish("well/log", "Well_Zero - " + str(datetime.now()).split(".")[0] + "\n" + str(device + " has been closed").capitalize())
                        record_time(device)

                    if m_decode[0] == "request":
                        if m_decode[1] == device and info[0] == "On":
                            record_time(device)

                        with open(device + "_time.txt", "r") as r:
                            client.publish("well/request", str(device + " " + info[0] + " " + r.readlines()[-1].split()[1]))
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
        GPIO.output(devices["valve1"][1], GPIO.HIGH)
        GPIO.output(devices["valve2"][1], GPIO.HIGH)

        for device, info in devices.items():
            devices[device] = ["Off", info[1]]
            record_time(device)

        if_disconnected = True # Sets if_disconnected to True for change in on_connect logback

    client = mqtt.Client("well_zero") # Sets up MQTT client

    # Sets up callbacks
    client.on_connect = on_connect
    client.on_log = on_log
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print("Connecting to broker", broker)

    while True:
        try:
            print("Attempt " + str(fail_con_startup))
            client.connect(broker) # Attempts to connect to MQTT broker
            print("Connection succesfull")
            break
        except OSError: # If connection to broker fails
            if fail_con_startup >= 5: # If there were five connection attempts
                print("Unable to connect to the broker. Trying again in approx. 15 minutes.")

                fail_log = open(str(datetime.now()).split(".")[0].replace(":", "-")[:10] + " - fail_log.txt", "a+")
                fail_log.write(str(datetime.now()) + " - Unable to connect to the broker. Trying again in approx. 15 minutes.\n")
                fail_log.close()

                # Closes both valves on disconnect
                GPIO.output(devices["valve1"][1], GPIO.HIGH)
                GPIO.output(devices["valve2"][1], GPIO.HIGH)

                for device, info in devices.items():
                    devices[device] = ["Off", info[1]]
                    record_time(device)

                GPIO.cleanup() # Cleans GPIO pins
                sys.exit() # Exits program cleanly
            else:
                print("Attempt failed. Trying again in 10 seconds.")
                fail_con_startup += 1 # += 1 to attempts
                time.sleep(10) # Waits ten seconds
                pass

    for f in os.listdir(path):
        for device, info in devices.items():
            if f == str(device + "_time.txt"):
                found = True
                break

    if not found:
        create_files()

    client.loop_start() # Starts MQTT loop

    while True:
        try:
            for device, info in devices.items():
                with open(device + "_time.txt", "r") as r:
                    if str(datetime.now())[5:10] != str(r.readlines()[-1]).split(" ")[0]:
                        with open(device + "_time.txt", "a+") as t:
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