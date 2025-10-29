import socket
import argparse
import threading
import time


# ADDITION: for timestamps and colored console output
from datetime import datetime
BLUE = "\033[94m"    # client-server send/receive
CYAN = "\033[96m"    # duplicate detection (for later)
RESET = "\033[0m"
GREEN = "\033[92m"  
YELLOW = "\033[93m"  # ADDITION: for manual input prompt
MAGENTA = "\033[95m"   # ADDITION: for manual sends

def ts():
    return datetime.now().strftime("%H:%M:%S")

# ADDITION: for optional manual input toggle
import sys, select

HOST = "127.0.0.1" #change to server ip
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

acks_received = {}
messages = []
req_num = 0
connected_sockets = [] 

# ADDITION: Thread for receiving data from each server replica

def receive_data(sock, server_id):
    global acks_received
    try:
        while True:
            # receive data
            data = sock.recv(1024)
            if not data:
                break
            else:
                res = data.decode().strip()
                 # ADDITION: unify log format
                print(f"{BLUE}[{ts()}] Client {client_id}: Received from Server {server_id} -> {res}{RESET}")

                # print("Received message:", res)
                # print(f"{BLUE}[{ts()}] Client {client_id}: Send ACK for received message{RESET}")
                if "Response to request" in res:
                    req_num = res.split("request")[1].split()[0]
                    server_id = res.split("Server")[1].split()[0]
                    acks_received[server_id] = res
                    if (len(acks_received) > 1):
                        print(f"Request {req_num}: Discarded duplicate message from server {server_id}")
                    else:
                        messages.append(res)
    except Exception as e:
          print(f"Error receiving data from Server {server_id}: {e}")

def manual_input():
    global req_num, client_id, connected_sockets
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            msg = sys.stdin.readline().strip()
            if msg.lower() == "exit":
                print(f"{YELLOW}Client {client_id} exiting manual mode...{RESET}")
                break
            elif msg:
                for i, sock in enumerate(connected_sockets, start=1):
                    message = f"<C{client_id}, S{i}, request{req_num}> {msg}"
                    try:
                        sock.sendall(message.encode())
                        print(f"{MAGENTA}[{ts()}] Client {client_id}: Sent manual {message} to Server {i}{RESET}")
                    except Exception as e:
                        print(f"{CYAN}Manual send failed to Server {i}: {e}{RESET}")
                req_num += 1
        time.sleep(0.1)

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Client")
    parser.add_argument("-i", "--id", type=int, default=1)
    #manual mode
    parser.add_argument("-m","--manual", action="store_true", default=False)

    args = parser.parse_args()
    global client_id
    client_id = args.id
    # ADDITION: simple request counter
    global req_num, connected_sockets

    servers = [(SERVER1_HOST, SERVER1_PORT, SERVER1_ID), (SERVER2_HOST, SERVER2_PORT, SERVER2_ID), (SERVER3_HOST, SERVER3_PORT, SERVER3_ID)]
    connected_sockets = []
    
    # connections to all 3 servers
    # added h, p , sid for easier understanding and printing
    
    for i, (h, p, sid) in enumerate(servers, start=1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            s.connect((h,p))
            print(f"{GREEN}Client {client_id} connected to Server {sid} at {h}:{p}{RESET}")
            connected_sockets.append(s)
            threading.Thread(target=receive_data, args=(s, sid)).start()
        except Exception as e:
            print(f"Server {sid} not available ({e})")

    # added manual entry function
    if args.manual:
        threading.Thread(target=manual_input, daemon=True).start()

    # message sending (continuous loop)
    while True:
        message = f"<C{client_id}, *, request{req_num}> Hello!"

        
        if len(connected_sockets) < len(servers):
            print(f"{CYAN}[{ts()}] Warning: Only {len(connected_sockets)} out of {len(servers)} servers connected{RESET}")

        # sending to the three servers...?
        # for i in range(len(servers)):
            # curr_socket = connected_sockets[i]
        for i, curr_socket in enumerate(connected_sockets, start=1):
            
            try:
                curr_socket.sendall(message.encode())
                print(f"{BLUE}[{ts()}] Client {client_id}: Sending {message}{RESET}")
            except Exception as e:
                print(f"Failed to send message to server {i+1}")

        # receive ACKs from three servers... ;-;
        # Wait until at least one ACK received
        start = time.time()
        while True:
            if str(req_num) in acks_received:
                print(f"{GREEN}[{ts()}] Received response from at least one server for request{req_num}{RESET}")
                # print(f"{GREEN}[{ts()}] All ACKS received for request{req_num}{RESET}")
                acks_received.clear()
                break
            # if time.time() - start > 30:
            #     print(f"{CYAN}[{ts()}] Timeout waiting for ACK for request{req_num}{RESET}")
            #     break
            time.sleep(0.5)
            
            # time.sleep(15)

        req_num += 1
        time.sleep(2)  # interval between requests


main()