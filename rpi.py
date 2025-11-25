'''
    LightSwarm Raspberry Pi Logger 
    SwitchDoc Labs 
    December 2020
'''
from __future__ import print_function
 
from builtins import chr
from builtins import str
from builtins import range
import sys  
import time 
import random
import matplotlib.pyplot as plt
from netifaces import interfaces, ifaddresses, AF_INET

from gpiozero import Button, LED

from signal import pause

from itertools import count
import datetime


from socket import *

VERSIONNUMBER = 7
# packet type definitions
LIGHT_UPDATE_PACKET = 0
RESET_SWARM_PACKET = 1
CHANGE_TEST_PACKET = 2   # Not Implemented
RESET_ME_PACKET = 3
DEFINE_SERVER_LOGGER_PACKET = 4
LOG_TO_SERVER_PACKET = 5
IS_MASTER = True
BLINK_BRIGHT_LED = 7
RESETFLAG = False
MYPORT = 2910
COLORS = ["gold", "green", "navy"]


def jsonBuilder(master_light, master_time):
    combined_data = []
    for light_values in master_light.values():
        combined_data.extend(light_values)

    # Generate labels as strings from "0" to "30"
    labels = [str(i) for i in range(31)]

    # Create the result in the specified format
    result = [{
        "series": ["Light Values"],
        "data": [combined_data],
        "labels": labels
    }]
    data = [[],[0],[0,0]]
    count = 0
    labels = []
    for uid, time in master_time.items():
        labels.append(uid)
        data[count].append(time)
        count += 1
    time_result = [{
        "series" : ["Master 1", "Master 2", "Master 3"],
        "data": data,
        "labels": labels
    }]
    final = str(result) + "|x|" + str(time_result)
    return final.replace("'", '"')
    
    
SWARMSIZE = 5

button = Button(4, bounce_time = 0.1)
white_led = LED(13)
yellow_led = LED(17)
red_led = LED(22)
green_led = LED(27)
START_GRAPH= False
DATA_FLAG = 0
START_LOG = -1
def on_button_pressed():
    global RESETFLAG
    global START_GRAPH
    global DATA_FLAG
    global START_LOG
    DATA_FLAG += 1
    START_GRAPH = True
    RESETFLAG = True
    print("RESET+++++++++++++++++")
    yellow_led.on()
    SendRESET_SWARM_PACKET(s)
    time.sleep(3)
    yellow_led.off()
    RESETFLAG = False
    START_LOG += 1
    


logString = ""
# command from command Code
# UDP Commands and packets

def SendDEFINE_SERVER_LOGGER_PACKET(s):
    print("DEFINE_SERVER_LOGGER_PACKET Sent") 
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

	# get IP address
    for ifaceName in interfaces():
            addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
            print('%s: %s' % (ifaceName, ', '.join(addresses)))
  
    # last interface (wlan0) grabbed 
    print(addresses) 
    myIP = addresses[0].split('.')
    print(myIP) 
    data= ["" for i in range(14)]

    
    data[0] = int("F0", 16).to_bytes(1,'little') 
    data[1] = int(DEFINE_SERVER_LOGGER_PACKET).to_bytes(1,'little')
    data[2] = int("FF", 16).to_bytes(1,'little') # swarm id (FF means not part of swarm)
    data[3] = int(VERSIONNUMBER).to_bytes(1,'little')
    data[4] = int(myIP[0]).to_bytes(1,'little') # 1 octet of ip
    data[5] = int(myIP[1]).to_bytes(1,'little') # 2 octet of ip
    data[6] = int(myIP[2]).to_bytes(1,'little') # 3 octet of ip
    data[7] = int(myIP[3]).to_bytes(1,'little') # 4 octet of ip
    data[8] = int(0x00).to_bytes(1,'little')
    data[9] = int(0x00).to_bytes(1,'little')
    data[10] = int(0x00).to_bytes(1,'little')
    data[11] = int(0x00).to_bytes(1,'little')
    data[12] = int(0x00).to_bytes(1,'little')
    data[13] = int(0x0F).to_bytes(1,'little')
    mymessage = ''.encode()  	
    s.sendto(mymessage.join(data), ('<broadcast>'.encode(), MYPORT))
	
def SendRESET_SWARM_PACKET(s):
    print("RESET_SWARM_PACKET Sent") 
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    data= ["" for i in range(14)]

    data[0] = int("F0", 16).to_bytes(1,'little')
    
    data[1] = int(RESET_SWARM_PACKET).to_bytes(1,'little')
    data[2] = int("FF", 16).to_bytes(1,'little') # swarm id (FF means not part of swarm)
    data[3] = int(VERSIONNUMBER).to_bytes(1,'little')
    data[4] = int(0x00).to_bytes(1,'little')
    data[5] = int(0x00).to_bytes(1,'little')
    data[6] = int(0x00).to_bytes(1,'little')
    data[7] = int(0x00).to_bytes(1,'little')
    data[8] = int(0x00).to_bytes(1,'little')
    data[9] = int(0x00).to_bytes(1,'little')
    data[10] = int(0x00).to_bytes(1,'little')
    data[11] = int(0x00).to_bytes(1,'little')
    data[12] = int(0x00).to_bytes(1,'little')
    data[13] = int(0x0F).to_bytes(1,'little')
      	
    mymessage = ''.encode()  	
    s.sendto(mymessage.join(data), ('<broadcast>'.encode(), MYPORT))
	
def listen():
    global RESETFLAG
    global DATA_FLAG
    global START_GRAPH
    global START_LOG
    photocell_data = []
    master_times = {}
    current_master = None
    master_light = {}
    time_index = count()
    flag = 1
    # Set up the plot
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    while(1) :
    # receive datclient (data, addr)
        if not RESETFLAG:
            d = s.recvfrom(1024)
            #print(d)
            message = d[0]
            addr = d[1]

            if (len(message) == 14):
                if (message[1] == LIGHT_UPDATE_PACKET):
                    if (message[3] == IS_MASTER):
                        MasterSwarmID = message[2]
                        #print(f"in LIGHT_UPDATE_PACKET, MASTER: {MasterSwarmID}")
                        if MasterSwarmID in swarmDict:
                            print(f"Master ID: {message[2]}")
                            print(f"LIGHT READING: {int(message[5] + message[6])}")
                            if START_GRAPH and START_LOG == 0:
                                if flag < DATA_FLAG:
                                    photocell_data = []
                                    master_times = {}
                                    current_master = None
                                    time_index = count()
                                    flag += 1
                                photocell_data, master_times, current_master, ax1, ax2 = update_graphs(int(message[5] + message[6]), message[2], photocell_data, master_times, current_master, COLORS[swarmDict.index(message[2])], time_index, fig, ax1, ax2)
                                if current_master in master_light:
                                    master_light[current_master].append(photocell_data[-1])
                                else:
                                    master_light[current_master] = []
                                    master_light[current_master].append(photocell_data[-1])
                            elif START_GRAPH and START_LOG == 1:
                                file_path = "Log/"
                                filename = file_path + str(datetime.datetime.now()) + ".txt"
                                f = open(filename, 'w')
                                txt = jsonBuilder(master_light, master_times)
                                f.write(txt)
                                f.close()
                                photocell_data = []
                                master_times = {}
                                master_light = {}
                                current_master = None
                                time_index = count()
                                photocell_data, master_times, current_master, ax1, ax2 = update_graphs(int(message[5] + message[6]), message[2], photocell_data, master_times, current_master, COLORS[swarmDict.index(message[2])], time_index, fig, ax1, ax2)
                                START_LOG -= 1
                            else:
                                photocell_data = []
                                master_times = {}
                                current_master = None
                                time_index = count()
                    if message[2] not in swarmDict:
                        swarmDict.append(message[2])
    
	
def update_graphs(light, master, photocell_data, master_times, 
                  current_master, color,  time_index, fig, ax1, ax2):
    # Initialize variables

        new_photocell_value = light
        photocell_data.append(new_photocell_value)

        new_master = str(master)
        if new_master != current_master:
            current_master = new_master

        # Update master times
        if current_master in master_times:
            master_times[current_master] += 1
        else:
            master_times[current_master] = 1

        # Keep only the last 30 seconds of data
        if len(photocell_data) > 30:
            photocell_data.pop(0)
        for master in list(master_times.keys()):
            if master != current_master and master_times[master] > 0 and sum(master_times.values()) > 30:
                master_times[master] -= 1
            if master_times[master] > 30:
                master_times[master] -= 1

        # Update photocell data trace
      #  ax1.clear()
      # ax1.plot(range(len(photocell_data)), photocell_data, color=color, linestyle='-', marker='o')
      #  ax1.set_title('Photocell Data Trace (Last 30 Seconds)')
      #  ax1.set_xlabel('Time (s)')
      #  ax1.set_ylabel('Photocell Value')
      #  ax1.grid(True)
        # Update master devices bar chart
      #  ax2.clear()
      #  ax2.bar(master_times.keys(), master_times.values(), color=color)
      #  ax2.set_title('Master Devices Over Time (Last 30 Seconds)')
      #  ax2.set_xlabel('Device IP')
      #  ax2.set_ylabel('Time as Master (s)')
      #  ax2.grid(True)

        # Refresh the plot
       # plt.pause(1)
        #plt.show()
        return photocell_data, master_times, current_master, ax1, ax2
        


if __name__ == "__main__":
    # set up sockets for UDP

    s=socket(AF_INET, SOCK_DGRAM)
    host = 'localhost'
    s.bind(('',MYPORT))

    print("--------------")
    print("LightSwarm Logger")
    print("Version ", VERSIONNUMBER)
    print("--------------")

    # first send out DEFINE_SERVER_LOGGER_PACKET to tell swarm where to send logging information 

    SendDEFINE_SERVER_LOGGER_PACKET(s)
    time.sleep(3)
    #SendDEFINE_SERVER_LOGGER_PACKET(s)


    swarmDict = []
    # 6 items per swarm item

    # 0 - NP  Not present, P = present, TO = time out
    # 1 - timestamp of last LIGHT_UPDATE_PACKET received
    # 2 - Master or slave status   M S
    # 3 - Current Test Item - 0 - CC 1 - Lux 2 - Red 3 - Green  4 - Blue
    # 4 - Current Test Direction  0 >=   1 <=
    # 5 - IP Address of Swarm
    button.when_pressed = on_button_pressed

    import threading
    threading.Thread(target=listen, daemon=True).start()


    pause()



    

