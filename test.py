from devices import Device

d1 = Device("d1", "D1", "valve", 55, "On")

valves = []

for i in Device.devices:
    if globals()[i].type == "valve":
        valves.append(i)

print(valves)