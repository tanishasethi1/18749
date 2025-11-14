import socket
import threading
import time
from datetime import datetime

from datetime import datetime
GREEN = "\033[92m"   # successful heartbeat
RED = "\033[91m"     # failure or timeout
YELLOW = "\033[93m"  # reconnect attempt
BLUE = "\033[94m"    # server ack
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1" #change to rm ip
PORT = 65085
TIMEOUT = 10

GFD_HOST = "127.0.0.1" #change to GFD ip
GFD_PORT = 65084

member_count = 0
membership = {}

def connect_to_gfd():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect((GFD_HOST, GFD_PORT))
            print(f"{GREEN}[{ts()}] RM: Connected to GFD at {GFD_HOST}:{GFD_PORT}{RESET}")
            return sock
        except Exception as e:
            print(f"{YELLOW}[{ts()}] RM: GFD not available yet ({e}); will retry...{RESET}")
            time.sleep(5)

def print_membership():
    # message format:
    # RM: x members - S1, S2, ...
    members = ""
    for lfd_id in membership.keys():
        members += f"S{lfd_id}, "

    print(f"RM: {len(membership)} members - {members[:-2]}")

# makes connection, registers which lfd, adds to membership list
def listen_for_updates(conn, addr):
    # handle updates
    member_count = 0
    members_list = None
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            # check if heartbeat is from a new LFD
            # need to determine who it's from, and whether it's a connect/disconnect message
            # data in format: "LFD<id>: Connected/Disconnected/Heartbeat"
            print("data :", data)
            lfd = data.split(":")[0].strip()
            lfd_id = lfd[-1]
            conn_status = data.split(":")[1].strip()
            
        
            # check if server connected to its LFD
            if "Server Connected" == conn_status:
                print(f"GFD: Server connected to LFD")
                if lfd_id not in membership.keys():
                    member_count += 1
                    membership[lfd_id] = 1
                    print_membership()
                    # print(f"GFD: {len(membership)} members")
            # check if LFD died/disconnected
            if "Server Disconnected" == conn_status:
                if lfd_id in membership.keys():
                    member_count -= 1
                    membership.pop(lfd_id)
                    print_membership()
                    # print(f"GFD: {len(membership)} members")
            # check if LFD heartbeat
            if "Heartbeat" == conn_status:
                 # ADDITION: respond to heartbeat so LFD can confirm
                conn.sendall("ACK".encode())
                print(f"{GREEN}[{ts()}] GFD: Heartbeat from LFD{lfd_id} {addr} acknowledged{RESET}")
                print_membership()
                # print(f"GFD: {len(membership)} members")

            # LFD connection check    
            if "Connected" == conn_status: 
                # if lfd_id not in membership.keys():
                #     member_count += 1
                #     membership[lfd_id] = 1
                #     print(f"GFD: {len(membership)} members")
                print(f"GFD: LFD {lfd_id} connected")
                
    except Exception as e:
        print(f"Error handling LFD {addr}: {e}")
            
    return 

def main():
    # connect to GFD   
    while True:
        gfd_sock = connect_to_gfd()
        listen_for_updates(gfd_sock)
        time.sleep(5)
    

main()

