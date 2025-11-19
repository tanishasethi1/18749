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

HOST = "172.26.66.140" #"127.0.0.1"
PORT = 65080

SERVER1_HOST = "172.26.3.40" #127.0.0.1"
SERVER1_PORT = 65081
SERVER1_ID = 1

SERVER2_HOST = "172.26.70.125" #"127.0.0.1"
SERVER2_PORT = 65082
SERVER2_ID = 2

SERVER3_HOST = "172.26.66.140" #"127.0.0.1"
SERVER3_PORT = 65083
SERVER3_ID = 3

TIMEOUT = 10
CHECKPOINT_FREQ = 5

backups = {1: [SERVER1_HOST, SERVER1_PORT, False, None], 2: [SERVER2_HOST, SERVER2_PORT, False, None], 3: [SERVER3_HOST, SERVER3_PORT, False, None]}

state_lock = threading.Lock()
my_state = 0
#active replica
i_am_ready = 1              
high_watermark = {}         
requested_checkpoint = False
passive = False

checkpoint_count = 0

primary = None # set to primary's id

clients = {}

def new_conn(conn, addr):
    global my_state, primary
    global i_am_ready, requested_checkpoint, high_watermark, checkpoint_count
    res = ""
    try:
        while True:
            # receive data
            data = conn.recv(1024)
            if not data:
                continue
            else:
                res = data.decode()

                #passive
                if "CHECKPOINT: state=" in res:
                    if not passive and "Leader" in res:
                        pass
                    else:
                        print(f"{CYAN}[{ts()}] Received message:{res} {RESET}")
                    updated_state = int(res.split("state=")[1].split()[0])
                    with state_lock:
                        my_state = updated_state
                else:
                    if not passive and "Leader" in res:
                        pass
                    else:
                        print("Received message: ", res)

                #active
                if res.startswith("CHECKPOINT "):
                    cp_state = int(res.split()[1])
                    print(f"[{ts()}] Server {id}: Installing recovery checkpoint state={cp_state}")
                    with state_lock:
                        my_state = cp_state
                    i_am_ready = 1
                    continue

                # prim respon to checkpoint req
                if res.startswith("REQUEST_CHECKPOINT"):
                    requester = int(res.split()[1])
                    cp_msg = f"CHECKPOINT {my_state}"
                    conn.sendall(cp_msg.encode())
                    print(f"[{ts()}] Server {id}: Sent recovery checkpoint to S{requester}")
                    continue

                if not passive and "Leader" in res:
                    pass
                else:
                    print("Received message:", res)

                #Update new leader
                if "New Leader" in res:
                    new_leader = res.split("New Leader: ")[1].strip().split('\n')[0]
                    new_leader = int(new_leader)
                    if new_leader != primary:
                        primary = new_leader
                        if passive:
                            print(f"{GREEN}[{ts()}] Server {id}: New Leader is server {primary} {primary == id}{RESET}")
                        if int(primary) == int(id):
                            if passive:
                                print(f"{GREEN}[{ts()}] Server {id}: I am the new Primary{RESET}")
                            threading.Thread(target=connect_to_backups).start()
                            threading.Thread(target=send_checkpoint).start()

                            #Notify clients
                            for client_id, client_conn in clients.items():
                                message = f"New Leader: {primary}\n"
                                client_conn.sendall(message.encode())
                                if passive:
                                    print(f"{BLUE}[{ts()}] Server {id}: Notified Client {client_id} of new leader {primary}{RESET}")
                        continue

                elif "Client" in res:
                    client_id = res.split("Client")[1].split(":")[0]
                    if client_id not in clients:
                        clients[client_id] = conn
                        print(f"{BLUE}[{ts()}] Server {id}: New client connected: Client {client_id}{RESET}")
                        # conn.sendall(f"New Leader: {primary}\n".encode())
                
                # LFD response handling
                if "Heartbeat" in res:
                    # ADDITION: respond to heartbeat so LFD can confirm
                    conn.sendall("ACK".encode())
                    print(f"{GREEN}[{ts()}] Server {id}: Heartbeat from LFD {id} {addr} acknowledged{RESET}")
                    continue
                # Client response handling
                #active recover log request
                if "request" in res:
                    try:
                        req_num_int = int(res.split("request")[1].split()[0])
                        client_id = res.split("C")[1].split(":")[0]
                        high_watermark[client_id] = req_num_int
                    except:
                        pass
                    
                    #if recovering do not reply
                    if not i_am_ready:
                        print(f"{YELLOW}[{ts()}] Server {id}: recovery mode — req {req_num_int}, not replying.{RESET}")
                        continue
                    
                    #normal
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
    global backups, primary, id, passive
    
    while primary == id:
        for backup_id in backups:
            if backup_id != primary:
                (host, port, connected, sock) = backups[backup_id]
                if (connected):
                    continue
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((host, port))
                    backups[backup_id][2] = True
                    backups[backup_id][3] = s
                    s.settimeout(TIMEOUT) 
                except Exception:
                    s.close()
                    continue
                    # print("Failed to set up secondary connection ", {e})
                

def send_checkpoint():
    global checkpoint_count
    global CHECKPOINT_FREQ
    global my_state
    global backups
    global id
    global passive
    if passive:
        print(f"{CYAN}[{ts()}] Server {id} starting checkpointing to backups...{RESET}")
    else:
        print(f"{CYAN}[{ts()}] Servers starting checkpointing to replicas...{RESET}")

    while primary == id:
        sleep(CHECKPOINT_FREQ)
        message = f"CHECKPOINT: state={my_state} checkpoint_count={checkpoint_count}"
        checkpoint_count+=1
        for backup_id in backups:
            (host, port, connected, sock) = backups[backup_id]
            if not connected:
                continue

            try:
                sock.sendall(message.encode())
                print(f"{CYAN}[{ts()}] Server {id} sending checkpoint to server {backup_id}{RESET}")
            except Exception as e:
                print("Failed to send checkpoint to server")

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("-i", "--id", type=int, default=1)
    parser.add_argument("-p", "--passive", action='store_true', help="Run server in passive mode")
    parser.add_argument("-ci", "--checkpoint-interval", type=int, default=5) #send checkpoints every 5 seconds
    parser.add_argument("--primary", type=int, default=1) #default primary is 1
    parser.add_argument("--recover", action="store_true")

    # parser.add_argument("-p", "--port", type=int, default=1)

    args = parser.parse_args()
    global id, primary, passive
    global i_am_ready, requested_checkpoint
    id = args.id
    primary = args.primary 
    passive = args.passive

    #flag
    if args.recover:
        global i_am_ready
        i_am_ready = 0
        print(f"{CYAN}[{ts()}] Server {id}: Starting in RECOVERY MODE (i_am_ready=0){RESET}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        if hasattr(socket, 'SO_REUSEPORT'):
            # Set SO_REUSEPORT to 1 (or True) to enable it
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:
            # Fallback to SO_REUSEADDR for older systems or certain platforms
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


        # bind socket to host and port
        s.bind((HOST, PORT+id))
        # listen for connections
        s.listen()

        # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # # bind socket to host and port (handle error if port already in use)
        # try:
        #    s.bind((HOST, PORT + id))
        # except OSError as e:
        #     print(f"{RED}[{ts()}] Failed to bind to {HOST}:{PORT+id}: {e}{RESET}")
        #     print(f"Hint: another process may be listening on that port. Check with `lsof -i :{PORT+id}` and stop it or choose a different --id.")
        #     return

        #ADDITION
        print(f"[{ts()}] Server listening on {HOST}:{PORT+id}")

        if passive:
            print(f"Server {id} started. Initial primary is Server {primary} (primary == id? {primary==id})")

        ### if recivering, req checkpoint from primary
        if i_am_ready == 0 and not requested_checkpoint:
            if passive:
                print("Recieving Primary Checkpoint")
            else:
                print("Recieving Checkpoint")

            def _req_cp():
                sleep(2)
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    primary_host = backups.get(primary)[0]
                    primary_port = backups.get(primary)[1]  
                    sock.connect((primary_host, primary_port))
                    sock.sendall(f"REQUEST_CHECKPOINT {id}".encode())
                    if passive:
                        print(f"{CYAN}[{ts()}] Server {id}: Requested checkpoint from primary {primary}{RESET}")
                    else:
                        print(f"{CYAN}[{ts()}] Server {id}: Requested checkpoint from active replicas {RESET}")
                    
                    # NEW: wait for checkpoint reply from primary
                    sock.settimeout(TIMEOUT)
                    reply = sock.recv(1024).decode()
                    print(f"{CYAN}[{ts()}] Server {id}: Received checkpoint reply: {reply}{RESET}")

                    if reply.startswith("CHECKPOINT "):
                        cp_state = int(reply.split()[1])
                        print(f"{GREEN}[{ts()}] Server {id}: getting recovery checkpoint state={cp_state}{RESET}")
                        global my_state, i_am_ready
                        with state_lock:
                            my_state = cp_state
                        i_am_ready = 1
                    else:
                        print(f"[{ts()}] Server {id}: recovery reply: {reply}")

                    sock.close()

                except Exception as e:
                    print(f"[{ts()}] Server {id}: Failed checkpoint request: {e}")
            threading.Thread(target=_req_cp).start()
            requested_checkpoint = True


        # if primary == id and args.passive:
        #     print(f"{GREEN}[{ts()}] Server {id}: I am the Primary: STARTING THREADS{RESET}")
        #     threading.Thread(target=connect_to_backups).start()
        #     threading.Thread(target=send_checkpoint).start()

        # accept connections in a loop
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            threading.Thread(target=new_conn, args=(conn, addr)).start()

main()