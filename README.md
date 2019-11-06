# Automatic Watering

This is a prototype for a much larger IoT project using the Raspberry Pi to control relays that open and close valves and running a Flask app in combination with the MQTT protocol to do so remotely

The two main parts of the project are the files valve.py and app.py.
For these two parts to be able to work together, both Pies have to be connected to the internet, and correct adresses to a MQTT broker have to be specified in code. 

## Valve.py

This is the file that is uploaded to the Raspberry Pi that controls the relays.

A more detailed explanation coming soon...

### Watchdog.py

Another file on aforementioned Pi is watchdog.py which checks if valve.py is or isn’t running.

If the program is not running, watchdog.py initializes it. 

Watchdog.py is ran on startup by the crontab tool and then every 15 minutes. (Not done in code, has to be done manually in your Pi.)

## App.py

This app is essentially uploaded to another Pi and it runs the Flask app that is used to control the relays.

Further explanation coming soon...








# TBD

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```
