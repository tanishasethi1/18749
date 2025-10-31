import socket
import threading
import argparse
from time import sleep
from datetime import datetime

# here is the StackOverflow I'm referencing:
# https://stackoverflow.com/questions/10810249/python-socket-multiple-clients

# whoever is hosting: do the following -->
# in terminal: ipconfig (windows) or ifconfig (mac)
# paste it into "host"

GREEN = "\033[92m"   # heartbeat
YELLOW = "\033[93m"  # state change
RED = "\033[91m"     # errors
BLUE = "\033[94m" 
RESET = "\033[0m"
CYAN = "\033[96m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1"
PORT = 65080

SERVER1_HOST = "127.0.0.1"
SERVER1_PORT = 65081
SERVER1_ID = 1

SERVER2_HOST = "127.0.0.1"
SERVER2_PORT = 65082
SERVER2_ID = 2

SERVER3_HOST = "127.0.0.1"
SERVER3_PORT = 65083
SERVER3_ID = 3

TIMEOUT = 10
CHECKPOINT_FREQ = 5

state_lock = threading.Lock()
my_state = 0

clients = []

connected_backups = []

checkpoint_count = 0

def new_conn(conn, addr):
    global my_state
    res = ""
    try:
        while True:
            # receive data
            data = conn.recv(1024)
            if not data:
                break
            else:
                res = data.decode()
                print("Received message:", res)
                # LFD response handling
                if res == "Heartbeat":
                    # ADDITION: respond to heartbeat so LFD can confirm
                    conn.sendall("ACK".encode())
                    print(f"{GREEN}[{ts()}] Server {id}: Heartbeat from LFD {id} {addr} acknowledged{RESET}")
                    continue
                # Client response handling
                elif "request" in res:
                    req_num = res.split("request")[1].split()[0]
                    client_id = res.split("C")[1].split(":")[0]
                    
                    # update client state
                    with state_lock:
                        current_state = my_state
                        my_state += 1
                    
                    print(f"{YELLOW}[{ts()}] Server {id}: State changed from {current_state} to {my_state}{RESET}")
                    reply = f"Server{id}: Response to request{req_num} from client {client_id}: {my_state}\n"
                    conn.sendall(reply.encode())
                    continue
                
            
    except ConnectionResetError:
        print(f"{addr} disconnected")
    finally:
        conn.close()

# for the primary:
# heartbeat/checkpointing message (similar to LFD)
# open second TCP connection for backup communication channel
# for each backup (2), send CHECKPOINT: state and increment checkpoint_count
# 

def connect_to_backups():
    # backups = [
    #         (SERVER2_HOST, SERVER2_PORT, 2, False, None),
    #         (SERVER3_HOST, SERVER3_PORT, 3, False, None)
    #     ]
    global backups
    backups = {2: [SERVER2_HOST, SERVER2_PORT, False, None], 3: [SERVER3_HOST, SERVER3_PORT, False, None]}

    while True:
        for id in backups:
            (host, port, connected, sock) = backups[id]
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                backups[id][2] = True
                backups[id][3] = s
                # connected_backups.append(s, id)
                s.settimeout(TIMEOUT) 
            except Exception:
                continue
                # print("Failed to set up secondary connection ", {e})
                
                

def send_checkpoint():
    global checkpoint_count
    global CHECKPOINT_FREQ
    global my_state

    while True:
        sleep(CHECKPOINT_FREQ)
        message = f"CHECKPOINT: state={my_state} checkpoint_count={checkpoint_count}"
        for backup_id, (host, port, connected, sock) in backups.items():
            if not connected:
                continue
            try:
                sock.sendall(message.encode())
                print(f"{CYAN}[{ts()}] Server {id} sending checkpoint to server{host}{RESET}")
                checkpoint_count+=1
            except Exception as e:
                print("Failed to send checkpoint to server")

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("-i", "--id", type=int, default=1)
    parser.add_argument("-p", "--passive", action='store_true', help="Run server in passive mode")
    parser.add_argument("-ci", "--checkpoint-interval", type=int, default=5) #send checkpoints every 5 seconds
    # parser.add_argument("-p", "--port", type=int, default=1)

    args = parser.parse_args()
    global id
    # global checkpoint_count
    # checkpoint_count= 0
    id = args.id
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # bind socket to host and port
        s.bind((HOST, PORT+id))
        # listen for connections
        s.listen()

        #ADDITION
        print(f"[{ts()}] Server listening on {HOST}:{PORT+id}")
        if (id == 1):
                threading.Thread(target=connect_to_backups).start()
                threading.Thread(target=send_checkpoint).start()

        # accept connections in a loop
        while True:
            conn, addr = s.accept()
            clients.append((conn, addr))
            threading.Thread(target=new_conn, args=(conn, addr)).start()

main()