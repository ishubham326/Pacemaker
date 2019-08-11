#!/usr/bin/env python3

"""
Implement the following:
✓   1. Enable the user to download parameters to the Pacemaker.
x   2. Request to see current parameters in the Pacemaker
✓   3. Request that the Pacemaker stream egram data, which must then be 
       displayed and printed (if requested by the user).
✓   4. Instruct the pacemaker to stop streaming egram data.
    5. Store and display/print a history of programmable parameters in the 
       Pacemaker.
        - we are only storing the current values
✓   6. Imitate (and tweak) srsVVI section 5 comms specs

Refer to packet_specification.txt for details on packet structure if you want 
answers and don't want to read the code. You can also call 
print_data_section_spec() if you want to print a description of the packet 
structure.

We implemented a read thread for the egram data stream since reading the port 
directly from the GUI slowed it down while the code waited for packets to 
come in. The read thread can gather and store packets without blocking GUI main
loop operation.

Details on threading:
https://www.tutorialspoint.com/python/python_multithreading.htm
"""

import serial
import time
import threading
from params import params as p
from params import params_by_pacing_mode as p_by_mode

# Internal Constants
k_egram = 0x47
k_echo = 0x49
k_estop = 0x62
k_pparams = 0x55
k_soh = 0x01
k_streamPeriod = 1 # millisecond (interval between egram samples)
k_sync = 0x16

port = "/dev/ttyACM0" # CHANGE THIS ONE TO COM_ FOR WINDOWS! 
baud = 115200
timeout = 0.1 # read waits 0.1 s for something in the buffer (++ efficient ++)

fn_code = {
            "rcv_params":k_pparams,
            "send_params":k_echo,
            "rqst_egram":k_egram,
            "stop_egram":k_estop,
          }


""" XOR checksum of an iterable of bytes """
def checksum(packet_bytes):
    c_sum = 0
    for byte in packet_bytes:
        c_sum = c_sum ^ byte 
    return c_sum
        
""" Command the Pacemaker to start sending egrams
Packet contains 4 header bytes with no data section.
    SYNC
    SOH
    FnCode
    Chksum
"""
def request_egram(): # not sure how to handle receiving it... periodic GUI function?
    packet = bytearray()
    packet.append(k_sync)
    packet.append(k_soh)
    packet.append(fn_code["rqst_egram"])
    packet.append(checksum(packet[0:3]))

    packet_len = len(packet)

    try:
        with serial.Serial(port=port, baudrate=baud, timeout=timeout) as s:
            s.write(packet)
            print(f"Writing: {packet}")
            s.flush()
        success = True
    except serial.serialutil.SerialException:
        success = False

    return success

""" 
Command the Pacemaker to stop sending egrams 
Packet contains 4 header bytes with no data section.
    SYNC
    SOH
    FnCode
    Chksum
"""
def stop_egram():
    packet = bytearray()
    packet.append(k_sync)
    packet.append(k_soh)
    packet.append(fn_code["stop_egram"])
    packet.append(checksum(packet[0:3]))

    packet_len = len(packet)

    try:
        with serial.Serial(port=port, baudrate=baud, timeout=timeout) as s:
            s.write(packet)
            print(f"Writing: {packet}")
            s.flush()
        success = True
    except serial.serialutil.SerialException:
        success = False

    return success

""" 
Construct a parameters packet based on the current mode. 
Reduce the message size by not transmitting parameters that aren't applicable 
to the current mode.
"""
def update_pacemaker_params():
    packet = bytearray()
    # construct header
    packet.append(k_sync)
    packet.append(k_soh)
    packet.append(fn_code["rcv_params"])
    packet.append(checksum(packet[0:3]))
    
    relevant_params = ["mode"]
    current_mode = p["mode"].get_str()
    relevant_params = relevant_params + p_by_mode[current_mode]

    # NOTE: parameters that have an "Off" option need a boolean byte in front
    # which tells us if they are to be used or not.
    for param_name in relevant_params:
        param_value = p[param_name].get()
        byte_size = p[param_name].get_max_value_size_in_bytes()
        
        # packet byte order is big endian
        for i in range(8*(byte_size-1),-1,-8):
            if param_value is None: # TODO change this behaviour to use 1 bool byte "Off" if param is None, "On" otherwise, followed by data bytes
                packet.append(0x00)
            else:
                packet.append(0xff & (param_value >> i))

    data_checksum = checksum(packet[4:])

    packet.append(data_checksum)

    packet_len = len(packet)
    
    try:
        with serial.Serial(port=port, baudrate=baud, timeout=timeout) as s:
            s.write(packet)
            print(f"Writing: {packet}")
            s.flush()
        success = True
    except serial.serialutil.SerialException:
        success = False

    return success

""" Lower priority to implement because we are currently just echoing params. """
def request_params():
    pass

""" Determine if the Pacemaker is connected for connection status light """
def pacemaker_connected():
    if EgramThread.port_in_use:
        connected = True
    else:
        try:
            serial_port = serial.Serial(port=port, 
                                        baudrate=baud, 
                                        timeout=timeout)
            serial_port.close()
            connected = True 
        except serial.serialutil.SerialException:
            connected = False

    return connected

""" Autogenerate packet documentation """
def print_data_section_spec():
    for mode in p_by_mode:
        relevant_params = p_by_mode[mode]
        byte_size = p["mode"].get_max_value_size_in_bytes()

        s = f"MODE: {mode}\n"
        s += f"    PARAMETER BYTES\n"
        s += f"    mode {byte_size}\n"
        for param_name in relevant_params:
            byte_size = p[param_name].get_max_value_size_in_bytes()
            s += f"    {param_name} {byte_size}\n"
        s += "    checksum 1\n"
        print(s)

""" 
Handles serial reads and buffers data so that the egram plot code can 
easily access it.
"""
class EgramThread(threading.Thread):
    port_in_use = False

    def __init__(self, packet_buffer_size):
        threading.Thread.__init__(self)
        self.egram_running = True
        self.packet_buffer_size = packet_buffer_size
        self.data_lock = threading.Lock()
        self.data = {"m_vraw":[], "m_araw":[]}

    """ Semaphore protected extraction of the egram plot data. """
    def get_data(self):
        data = None
        with self.data_lock:
            # create new name for self.data
            data = self.data
            # make self.data point to a new empty structure
            self.data = {"m_vraw":[], "m_araw":[]}
        return data

    """ Set a flag to stop the egram """
    def quit(self):
        self.egram_running = False

    """ 
    Overrides the Thread method which is called by thread.start() 
    Read egram_packet_len bytes at a time from the serial port. When you have 
    self.packet_buffer_size packets, use a Python memoryview to efficiently read
    the packet buffer. Find the first occurring header, then read out the data
    section into a field of the class called self.data. This field contains the
    m_vraw and m_araw data from the Pacemaker for the two egram plot lines.
    The structure self.data is protected by a thread lock so that other threads
    can access it with self.get_data().
    """
    def run(self):
        egram_header_len = 2
        egram_data_len = 4
        egram_packet_len = egram_header_len + egram_data_len
        packets = b''
        num_packets = 0
        EgramThread.port_in_use = True
        try:
            serial_port = serial.Serial(port=port, 
                                        baudrate=baud, 
                                        timeout=timeout)

            while(self.egram_running):
                if num_packets >= self.packet_buffer_size:
                    buff = memoryview(packets)  # more efficient slicing
                    state = 0 
                    while (len(buff)) > egram_packet_len: 
                        if state == 0:
                            if buff[0] == k_sync:
                                state = 1
                            buff = buff[1:]
                        elif state == 1:
                            if buff[0] == k_soh:
                                state = 2
                            buff = buff[1:]
                        elif state == 2:
                            #print(f"{buff[0]} {buff[1]} {buff[2]} {buff[3]}")
                            state = 0
                            m_vraw = (buff[0] << 8) + buff[1]
                            m_araw = (buff[2] << 8) + buff[3]
                            with self.data_lock:
                                self.data["m_vraw"].append(m_vraw)
                                self.data["m_araw"].append(m_araw)
                            buff = buff[egram_data_len:]
                    packets = packets[-len(buff):]
                    num_packets = 0

                packets = packets + serial_port.read(egram_packet_len)
                num_packets = num_packets + 1

            serial_port.close()

        except serial.serialutil.SerialException:
            print("Device Disconnected!") 

        finally:
            EgramThread.port_in_use = False

if __name__ == "__main__":
    print_data_section_spec()

    request_egram()

    time.sleep(0.5)

    thread = EgramThread(256)
    thread.start()
    for i in range(10):
        data = thread.get_data()
        print("m_vraw: {}".format(data["m_vraw"]))
        print("m_araw: {}".format(data["m_araw"]))
        time.sleep(0.5)
    thread.quit()

    time.sleep(0.5)

    stop_egram()

    time.sleep(0.5)

    p["mode"].set("VVI")

    update_pacemaker_params()
