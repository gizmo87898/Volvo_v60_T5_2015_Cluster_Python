import time
import can
import random 
import socket
import struct
import select 
import threading
import tkinter as tk
from tkinter import ttk
import win_precise_time as wpt
from datetime import datetime
from collections import defaultdict

bus = can.interface.Bus(channel='com7', bustype='seeedstudio', bitrate=125000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 4567))
message_analytics = defaultdict(lambda: {"count": 0, "last_received": None, "data": None, "delay_sum": 0})

start_time_100ms = time.time()
start_time_10ms = time.time()
start_time_5s = time.time()

id_counter = 0x3d
counter_4bit = 0

ignition = True
rpm = 780
speed = 0
gear = b'0'
gearSelector = b"P"
coolant_temp = 90
oil_temp = 90
fuel = 100
drive_mode = 2

left_directional = False
lowpressure = False
right_directional = False
tc = False
abs = False
battery = False
handbrake = False
highbeam = False
outside_temp = 72

foglight = False
rear_foglight = False
lowbeam = False 
check_engine = False
hood = False
trunk = False

airbag = False
seatbelt = False


# Thread for receiving CAN messages
def receive():
    while True:
        message = bus.recv()
        print(message)

receive_thread = threading.Thread(target=receive)    
receive_thread.start()

# Function to update the table with message analytics
def update_table(id):
    global tree
    hexid = hex(id)
    #find a row in the id column matching hexid

def gui_thread():
    # Create GUI objects here
    root = tk.Tk()
    root.title("CAN Message Analytics")
    
    global tree  # Declare tree as global
    
    tree = ttk.Treeview(root, columns=("ID", "Avg Delay", "DLC", "Last Received", "Data"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Avg Delay", text="Avg Delay")
    tree.heading("DLC", text="DLC")
    tree.heading("Last Received", text="Last Received")
    tree.heading("Data", text="Data")
    tree.pack(expand=True, fill="both")

    root.mainloop()


gui_thread = threading.Thread(target=gui_thread)    
gui_thread.start()

while True:
    current_time = time.time()
    ready_to_read, _, _ = select.select([sock], [], [], 0)
    if sock in ready_to_read:
        data, _ = sock.recvfrom(256)
        packet = struct.unpack('2c7f2I3f', data)
        rpm = int(max(min(packet[3], 8000), 0))
        speed = packet[2]
        coolant_temp = int(packet[5])
        oil_temp = int(packet[8])
        fuel = int(packet[6]*100)
        gearSelector = packet[0]
        gear = packet[1]
        left_directional = False
        right_directional = False
        highbeam = False
        abs = False
        battery = False
        tc = False
        handbrake = False
        shiftlight = False
        ignition = False
        lowpressure = False
        check_engine = False
        foglight = False
        lowbeam = False
        
        if (packet[10]>>0)&1:
            shiftlight = True
        if (packet[10]>>1)&1:
            highbeam = True
        if (packet[10]>>2)&1:
            handbrake = True
        if (packet[10]>>4)&1:
            tc = True
        if (packet[10]>>10)&1:
            abs = True
        if (packet[10]>>9)&1:
            battery = True
        if (packet[10]>>5)&1:
            left_directional = True
        if (packet[10]>>6)&1:
            right_directional = True
        if (packet[10]>>11)&1:
            ignition = True
        if (packet[10]>>12)&1:
            lowpressure = True
        if (packet[10]>>13)&1:
            check_engine = True
        if (packet[10]>>14)&1:
            foglight = True
        if (packet[10]>>15)&1:
            lowbeam = True

    # Send each message every 100ms
    elapsed_time_100ms = current_time - start_time_100ms
    if elapsed_time_100ms >= 0.1:
        date = datetime.now()

        messages_100ms = [
            can.Message(arbitration_id=0xfd, data=[ # ignition and washer fluid message on first byte
                0,0b10011011,0,0,0,0,0,0], is_extended_id=False),
            can.Message(arbitration_id=0x110, data=[ # messages, ignition?
                0xff,0xff,0,0,0,0,0,0], is_extended_id=False),
            can.Message(arbitration_id=id_counter, data=[
                random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)], is_extended_id=False),
        ]
        
        counter_4bit = (counter_4bit + 1) % 16
        # Send Messages
        for message in messages_100ms:
            bus.send(message)
            wpt.sleep(0.001)
        start_time_100ms = time.time()

    # Execute code every 10ms
    elapsed_time_10ms = current_time - start_time_10ms
    if elapsed_time_10ms >= 0.01:  # 10ms
        messages_10ms = [
            can.Message(arbitration_id=0x141, data=[ # RPM
                0,0,0,0, rpm & 0xFF,(rpm >> 8) & 0xFF,0,0], is_extended_id=False),    
        ]
        for message in messages_10ms:
            bus.send(message)
            wpt.sleep(0.001)
        start_time_10ms = time.time()

    # Execute code every 5s
    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 4:
        id_counter += 1
        print(hex(id_counter))
        if id_counter == 0x7ff:
            id_counter = 0
        start_time_5s = time.time()
