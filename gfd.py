import socket
import threading

from datetime import datetime
GREEN = "\033[92m"   # successful heartbeat
RED = "\033[91m"     # failure or timeout
YELLOW = "\033[93m"  # reconnect attempt
BLUE = "\033[94m"    # server ack
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1" #change to server ip
PORT = 65084
TIMEOUT = 10

member_count = 0
membership = {}
lock = threading.Lock()

def print_membership():
    # message format:
    # GFD: x members - S1, S2, ...
    members = ""
    for lfd_id in membership.keys():
        members += f"S{lfd_id}, "

    print(f"GFD: {len(membership)} members - {members[:-2]}")

# makes connection, registers which lfd, adds to membership list
def handle_lfd(conn, addr):
    member_count = len(membership)
    # handle heartbeats
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
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"GFD listening on {HOST}:{PORT}")
        
        # connecting LFDs
        while True:
            conn, addr = s.accept()
            # with conn:
            print(f"Connected by {addr}")
            threading.Thread(target=handle_lfd, args=(conn, addr)).start()            
            
    return

main()