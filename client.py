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

def ts():
    return datetime.now().strftime("%H:%M:%S")

# 
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

def receive_data(sock, server_id):
    global acks_received
    try:
        while True:
            # receive data
            data = sock.recv(1024)
            if not data:
                break
            else:
                res = data.decode()
                print("Received message:", res)
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
          print(f"Error receiving data: {e}")

def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Client")
    parser.add_argument("-i", "--id", type=int, default=1)

    args = parser.parse_args()
    global client_id
    client_id = args.id
    # ADDITION: simple request counter
    req_num = 0

    servers = [(SERVER1_HOST, SERVER1_PORT, SERVER1_ID), (SERVER2_HOST, SERVER2_PORT, SERVER2_ID)]#, (SERVER3_HOST, SERVER3_PORT, SERVER3_ID)]
    connected_sockets = []
    
    # connections to all 3 servers
    for i in range(len(servers)):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            s.connect((servers[i][0], servers[i][1]))
            print(f"Client {client_id} connected to server {i+1} at {servers[i][0]}:{servers[i][1]}")
            connected_sockets.append(s)

            threading.Thread(target=receive_data, args=(s, servers[i][2])).start()
        except Exception as e:
            print(f"Server {i+1} not available")

    # message sending (continuous loop)
    while True:
        message = f"C{client_id}: request{req_num} --> Hello!"

        # sending to the three servers...?
        for i in range(len(servers)):
            curr_socket = connected_sockets[i]
            try:
                curr_socket.sendall(message.encode())
                print(f"{BLUE}[{ts()}] Client {client_id}: Sending {message}{RESET}")
            except Exception as e:
                print(f"Failed to send message to server {i+1}")

        # receive ACKs from three servers... ;-;
        while True:
            if len(acks_received) >= 1:
                print(f"{GREEN}[{ts()}] Received response from at least one server for request{req_num}{RESET}")
                # print(f"{GREEN}[{ts()}] All ACKS received for request{req_num}{RESET}")
                acks_received.clear()
                break
            
            # time.sleep(15)

        req_num += 1

main()