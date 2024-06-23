import time
import can
import random
import socket
import struct
import select
import threading
import tkinter as tk
import win_precise_time as wpt
from datetime import datetime

bus = can.interface.Bus(channel='com7', bustype='seeedstudio', bitrate=125000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 4567))

# Track time for each function separately
start_time_100ms = time.time()
start_time_10ms = time.time()
start_time_5s = time.time()

id_counter = 0
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

button_bits = [0] * 8  # Initialize bits for the buttons

def gui_thread():
    def toggle_bit(index):
        button_bits[index] = 1 if button_bits[index] == 0 else 0
        update_message()

    def update_message():
        # Update button states in the 0x23 message
        button_byte = 0
        for i in range(8):
            if button_bits[i]:
                button_byte |= (1 << i)
        message_data = [0, button_byte, 0, 0, 0, 0, 0, 0]
        message = can.Message(arbitration_id=0x23, data=message_data, is_extended_id=False)
        bus.send(message)
        return button_byte

    root = tk.Tk()
    root.title("G30")

    for i in range(8):
        button = tk.Button(root, text=f"Button {i+1}", command=lambda i=i: toggle_bit(i))
        button.grid(row=i // 4, column=i % 4)

    root.mainloop()

gui_thread = threading.Thread(target=gui_thread)
gui_thread.start()

def receive():
    while True:
        message = bus.recv()
        #print(message)
receive = threading.Thread(target=receive)    
receive.start()

while True:
    current_time = time.time()
    
    ready_to_read, _, _ = select.select([sock], [], [], 0)
    if sock in ready_to_read:
        data, _ = sock.recvfrom(256)
        packet = struct.unpack('2c7f2I3f', data)
        rpm = int(max(min(packet[3], 8000), 0))
        speed = packet[2]*1.41
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

    elapsed_time_100ms = current_time - start_time_100ms
    if elapsed_time_100ms >= 0.1:
        date = datetime.now()
        
        # Update button states in the 0x23 message
        button_byte = 0
        for i in range(8):
            if button_bits[i]:
                button_byte |= (1 << i)
        
        messages_100ms = [
            can.Message(arbitration_id=0x23, data=[ # steering wheel buttons and directionals
                0,button_byte,0,0,0,0,0,0], is_extended_id=False), # Make the buttons change these bits

            can.Message(arbitration_id=0x110, data=[ # brightness
                0xff,0,0,0,0,0,0,0], is_extended_id=False),
            
            can.Message(arbitration_id=0x153, data=[ # ?, dstc sport, 
                random.randint(0,255),0b11101010 + highbeam,0xaa,0xaa,0xaa,0xaa,0xaa,0xaa], is_extended_id=False),

            can.Message(arbitration_id=0x310, data=[ # speed
                random.randint(0,255),random.randint(0,255),0,int(speed) & 0xFF,(int(speed) >> 4) & 0xFF,0xff,0,random.randint(0,255)], is_extended_id=False),

            can.Message(arbitration_id=0x4a0, data=[ # fuel level and low coolant message
                random.randint(0,255),0,0,0,0,0x01,0xcf,0], is_extended_id=False),

            can.Message(arbitration_id=0x31c, data=[ # language
                0,0,1,0,0,0,0,0], is_extended_id=False),

            can.Message(arbitration_id=0xfd, data=[ # RPM and ignition
                random.randint(0,255),0x9c,0,0,0,(rpm >> 8) & 0xFF,rpm & 0xFF,0xe0], is_extended_id=False),

            can.Message(arbitration_id=id_counter, data=[
                random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255)], is_extended_id=False),
        ]

        counter_4bit = (counter_4bit + 1) % 16
        for message in messages_100ms:
            bus.send(message)
            wpt.sleep(0.001)
        start_time_100ms = time.time()

    # Execute code every 10ms
    elapsed_time_10ms = current_time - start_time_10ms
    if elapsed_time_10ms >= 0.01:  # 10ms
        messages_10ms = [
                
            
        ]
        for message in messages_10ms:
            bus.send(message)
            wpt.sleep(0.001)
        start_time_10ms = time.time()

    # Execute code every 5s
    elapsed_time_5s = current_time - start_time_5s
    if elapsed_time_5s >= 2:
        id_counter += 1
        print(hex(id_counter))
        if id_counter == 0x7ff:
            id_counter = 0

        start_time_5s = time.time()
