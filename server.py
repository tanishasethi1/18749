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
PORT = 65083

state_lock = threading.Lock()
my_state = 0

def new_client(conn, addr):
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

                if res == "Heartbeat":
                    # ADDITION: respond to heartbeat so LFD can confirm
                    conn.sendall("ACK".encode())
                    print(f"{GREEN}[{ts()}] Server 1: Heartbeat from LFD 1 {addr} acknowledged{RESET}")
                    continue
            
            with state_lock:
                current_state = my_state
                my_state += 1
            print(f"Server state before reply: {current_state}")

            # ADDITION: showin afterstate 
            print(f"{YELLOW}[{ts()}] Server 1: State changed from {current_state} to {my_state}{RESET}")


            # echo data back 
            reply = f"Message received from S1. Server state: {current_state}"
            reply += "\n"
            conn.sendall(reply.encode())
            conn.sendall(res.encode())
            print("Echoed to client")
    except ConnectionResetError:
        print(f"{addr} disconnected")
    finally:
        conn.close()

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("-s", "--server", type=int, default=1)


    args = parser.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # bind socket to host and port
        s.bind((HOST, PORT))
        # listen for connections
        s.listen()

        #ADDITION
        print(f"[{ts()}] Server listening on {HOST}:{PORT}")

        # accept connections in a loop
        while True:
            conn, addr = s.accept()
            print(f"Connected to client")
            threading.Thread(target=new_client, args=(conn, addr)).start()

main()