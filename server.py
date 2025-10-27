import socket
import threading
import argparse

# here is the StackOverflow I'm referencing:
# https://stackoverflow.com/questions/10810249/python-socket-multiple-clients

# whoever is hosting: do the following -->
# in terminal: ipconfig (windows) or ifconfig (mac)
# paste it into "host"

from datetime import datetime
GREEN = "\033[92m"   # heartbeat
YELLOW = "\033[93m"  # state change
RED = "\033[91m"     # errors
RESET = "\033[0m"

def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1"
PORT = 65080

state_lock = threading.Lock()
my_state = 0

clients = []

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

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("-i", "--id", type=int, default=1)
    # parser.add_argument("-p", "--port", type=int, default=1)

    args = parser.parse_args()
    global id
    id = args.id
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # bind socket to host and port
        s.bind((HOST, PORT+id))
        # listen for connections
        s.listen()

        #ADDITION
        print(f"[{ts()}] Server listening on {HOST}:{PORT+id}")

        # accept connections in a loop
        while True:
            conn, addr = s.accept()
            print(f"Connected to something")
            clients.append((conn, addr))
            threading.Thread(target=new_conn, args=(conn, addr)).start()

main()