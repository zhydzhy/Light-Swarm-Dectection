# LightSwarm: Distributed Light Sensor Swarm System  
*A Raspberry Pi + ESP/Arduino–based distributed sensor network with real-time UDP communication and centralized logging.*

---

## Overview

LightSwarm is a distributed light-sensing network composed of a **Raspberry Pi master/logger** and multiple **ESP/Arduino swarm nodes** equipped with photocell sensors. Each node continuously captures light intensity, broadcasts readings over UDP, and participates in a simple master-election process.

The Raspberry Pi coordinates the swarm by:

- Auto-discovering swarm devices  
- Sending RESET and DEFINE packets  
- Collecting photocell readings in real time  
- Tracking which device is “master” at each timestep  
- Generating structured JSON logs  
- (Optionally) plotting live graphs of reading histories  

This project showcases essential IoT concepts:  
**distributed sensing**, **UDP broadcast networking**, **embedded LED feedback**, **real-time logging**, and **Raspberry Pi GPIO integration**.




---

##  Features

###  Distributed Light Sensing
Each swarm node broadcasts photocell values using a lightweight UDP protocol.

###  Swarm Reset + Auto-Discovery
The Raspberry Pi can instruct all nodes to reset and re-announce themselves.

###  Real-Time UDP Communication
- Broadcast protocol  
- Port: **2910**  
- Packet size: **14 bytes**  
- Header byte: `0xF0`

###  Live Graphing & Logging
The Pi stores:

- Last **30 seconds** of photocell readings  
- Per-node time spent as master  
- JSON logs in `/Log/`  

### Raspberry Pi LED Indicators
- **Yellow LED** = Reset in progress  
- Additional LEDs for debugging & state indication  

---

##  Packet Structure (14 Bytes)

| Byte | Description |
|------|-------------|
| 0 | Start byte (`0xF0`) |
| 1 | Packet type (`LIGHT_UPDATE_PACKET`, etc.) |
| 2 | Swarm Node ID |
| 3 | Version / master flag |
| 4–7 | Raspberry Pi IP address |
| 8–13 | Reserved / sensor data |

---

##  Raspberry Pi Code (rpi.py)

### Key Components

####  Packet Transmissions
- `SendDEFINE_SERVER_LOGGER_PACKET()`  
- `SendRESET_SWARM_PACKET()`

####  UDP Listener
`listen()` continuously processes packets and extracts:

- Light readings  
- Active master node  
- Per-node master duration  
- Membership updates  

####  Data Tracking
The Pi maintains:

- Sliding window of last 30 readings  
- Per-device master counter  
- Combined JSON log output (`jsonBuilder()`)

####  Hardware Interaction
- Button on GPIO 4 triggers RESET  
- LEDs indicate event states  

---

##  Output Logging Format

`jsonBuilder()` produces the following two-part JSON string:
[
{
"series": ["Light Values"],
"data": [[ ... last 30 values ... ]],
"labels": ["0", "1", ..., "30"]
}
]
|x|
[
{
"series": ["Master 1", "Master 2", "Master 3"],
"data": [ [ ... ], [ ... ], [ ... ] ],
"labels": ["NodeA", "NodeB", "NodeC"]
}
]


This format can be consumed by dashboards such as Node-RED.

---

## Setup Instructions

### **1. Raspberry Pi Setup**

Install dependencies:

```bash
sudo apt-get update
sudo apt-get install python3-gpiozero python3-netifaces
pip3 install matplotlib
```
Run the logger
```python
python3 rpi.py
```
## 2. ESP/Arduino Swarm Node Setup

The `LightSwarm.ino` file contains the firmware that each swarm device runs.  
Every node must:

- Join the same Wi-Fi network as the Raspberry Pi  
- Have a **unique Swarm ID**  
- Continuously read from a photocell (LDR)  
- Broadcast sensor readings via UDP  
- Respond to RESET packets from the Raspberry Pi  

###  Firmware Overview

Each ESP/Arduino node performs the following:

1. **Connects to Wi-Fi**
2. **Initializes LEDs & photocell input**
3. **Listens for Raspberry Pi commands**  
   - `DEFINE_SERVER_LOGGER_PACKET`  
   - `RESET_SWARM_PACKET`
4. **Broadcasts `LIGHT_UPDATE_PACKET`** every cycle  
5. **Participates in master election**  
   (based on internal logic — usually dependent on reading changes)
6. **Sends its photocell value + ID** to the Pi

###  Required Hardware (Per Node)

- ESP8266 / ESP32 / Arduino + WiFi module  
- 1× photocell (LDR)  
- 1× 10kΩ resistor (voltage divider for photocell)  
- LEDs for indication (white, yellow, red, green depending on your wiring)  
- Breadboard + jumper wires  

###  Basic Wiring
Photocell → A0  
LEDs → Digital pins (defined in `LightSwarm.ino`)  
Wi-Fi → Built-in module (ESP8266/ESP32) or external shield 

<img width="1225" height="762" alt="image" src="https://github.com/user-attachments/assets/3b18dd51-3656-4631-9f4d-f9c65afb5ffa" />

Typical photocell voltage-divider circuit:
3.3V ----[ LDR ]---- A0 ----[ 10kΩ ]---- GND


<img width="1217" height="750" alt="image" src="https://github.com/user-attachments/assets/64ad4a62-3fe2-49bc-99e2-0e650006218c" />

### Uploading the Firmware

1. Open the Arduino IDE (or PlatformIO).
2. Install the required board package for your device:
   - ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)
   - ESP32 Boards → ESP32 Dev Module
3. Connect the device via USB and select the correct COM port.
4. Open `LightSwarm.ino`.
5. Update the configuration inside the sketch:
   - Set the correct Wi-Fi SSID and password.
   - Assign a unique swarm ID to this node.
   - Verify that the pin definitions match your wiring (LED pins, photocell input).
6. Click Upload to flash the firmware onto the device.
7. Open the Serial Monitor to confirm that the device:
   - Connects to Wi-Fi
   - Reports its swarm ID
   - Begins broadcasting UDP packets

---

### Packet Broadcast Behavior

Each swarm node sends a structured 14-byte UDP packet at regular intervals. The packet has the following layout:

| Byte | Description |
|------|-------------|
| 0 | Start byte `0xF0` |
| 1 | Packet type (`LIGHT_UPDATE_PACKET` etc.) |
| 2 | Swarm node ID |
| 3 | Version number or master flag |
| 4–7 | Raspberry Pi logger IP address |
| 8–9 | Photocell reading (high byte + low byte) |
| 10–13 | Reserved for future features |

Broadcast target:

Address: 255.255.255.255
Port: 2910
Protocol: UDP


---

### Node Responsibilities

Each ESP/Arduino swarm node performs the following operations:

- Initializes Wi-Fi and joins the same network as the Raspberry Pi.
- Reads photocell data from its analog input pin.
- Sends periodic `LIGHT_UPDATE_PACKET` messages to the Pi.
- Responds to swarm control packets:
  - `RESET_SWARM_PACKET`
  - `DEFINE_SERVER_LOGGER_PACKET`
- Maintains internal counters for timing and master-role behavior.
- Optionally uses LEDs for debugging and state indications.

<img width="1214" height="665" alt="image" src="https://github.com/user-attachments/assets/7f5712d0-b4a3-4d55-907e-f00f6c8f10f8" />


### Raspberry Pi Logger (Python)

The Raspberry Pi runs `rpi.py`, which acts as the central controller and data logger for the entire LightSwarm system. It listens for incoming UDP packets, tracks active swarm nodes, manages resets, and generates structured log files.

#### Responsibilities of the Raspberry Pi

- Sends `DEFINE_SERVER_LOGGER_PACKET` at startup so nodes know where to report.
- Listens for incoming UDP packets from all swarm nodes.
- Maintains a sliding 30-second window of photocell readings.
- Tracks how long each node remains the “master” device.
- Handles button-based swarm resets (via GPIO input).
- Controls LEDs to indicate system events (reset, logging, etc.).
- Outputs JSON-formatted logs into the `Log/` directory.

<img width="1241" height="786" alt="image" src="https://github.com/user-attachments/assets/f2bc276e-ef2d-4631-8647-83a4f6ade282" />

---

### Logger Initialization

When `rpi.py` starts, it performs the following:

1. Opens a UDP socket on port `2910`.
2. Broadcasts a `DEFINE_SERVER_LOGGER_PACKET`, which includes the Pi's IP address.
3. Waits three seconds for swarm nodes to acknowledge.
4. Begins continuous listening for incoming packets in a background thread.
5. Sets up GPIO hardware:
   - Button on GPIO 4 to trigger swarm reset.
   - LEDs on GPIO 13, 17, 22, 27 for state indication.

The script enters an infinite loop where it listens, processes data, tracks timing, and handles resets.

---

### Reset Behavior

Pressing the physical button triggers:

1. LED indication (yellow LED on during reset).
2. Broadcast of `RESET_SWARM_PACKET`.
3. Reset of internal timers and buffers.
4. Full restart of logging and graph windows.

This ensures every swarm device begins reporting from a synchronized baseline.

---

### Log Output Format

The logger writes its output using the `jsonBuilder()` function, which produces two JSON structures separated by `|x|`.

Example log format:

[
{
"series": ["Light Values"],
"data": [[ ... last 30 photocell readings ... ]],
"labels": ["0", "1", ..., "30"]
}
]
|x|
[
{
"series": ["Master 1", "Master 2", "Master 3"],
"data": [
[ ... master time for node A ... ],
[ ... master time for node B ... ],
[ ... master time for node C ... ]
],
"labels": ["NodeA", "NodeB", "NodeC"]
}
]

These logs are stored in:

Log/YYYY-MM-DD HH:MM:SS.txt


Each file corresponds to one completed logging cycle.

---

### Real-Time Visualization (Optional)

The script includes commented-out matplotlib visualization code.  
If enabled, it displays:

1. A real-time line graph of the last 30 photocell readings.
2. A bar chart showing how many seconds each device spent as master.

To enable live plotting:

- Uncomment the plotting lines inside `update_graphs()`.



---

### Next Steps and Improvements

Potential enhancements for future versions:

- MQTT integration for cloud dashboards.
- Web-based real-time visualization panel.
- SD card log rotation and long-term storage.
- OTA updates for ESP/Arduino nodes.
- More advanced master-election algorithms.
- Device heartbeat and failure detection.

