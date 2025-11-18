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
YELLOW = "\033[93m"

def ts():
    return datetime.now().strftime("%H:%M:%S")


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

servers = [(SERVER1_HOST, SERVER1_PORT, SERVER1_ID), (SERVER2_HOST, SERVER2_PORT, SERVER2_ID), (SERVER3_HOST, SERVER3_PORT, SERVER3_ID)]
connected_sockets = {}
leader_id = SERVER1_ID

acks_received = {}
messages = []

def receive_data(sock, server_id):
    global acks_received, leader_id
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
                if "New Leader: " in res:
                    new_leader = res.split("New Leader: ")[1].strip()
                    leader_id = int(new_leader)
                    print(f"{GREEN}[{ts()}] Client {client_id}: Updated leader to Server {leader_id}{RESET}")
    except Exception as e:
          print(f"Error receiving data: {e}")
    finally:
        try:
            sock.close()
        except OSError:
            pass
        if connected_sockets.get(server_id) is sock:
            del connected_sockets[server_id]
            print(f"[{ts()}] Client {client_id}: Removed dead connection for server {server_id}")


def connect_to_servers():
    global servers, connected_sockets

    while True:
        if len(connected_sockets) == len(servers):
            time.sleep(30)
            continue

        # connections to all 3 servers
        for i in range(len(servers)):
            if (i+1) in connected_sockets:
                continue
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                s.connect((servers[i][0], servers[i][1]))
                print(f"Client {client_id} connected to server {i+1} at {servers[i][0]}:{servers[i][1]}")
                connected_sockets[i+1] = s
                s.sendall(f"Client{client_id}: Connected".encode())
                threading.Thread(target=receive_data, args=(s, servers[i][2])).start()
            except Exception as e:
                pass
            time.sleep(5)


def send_requests(passive):
    # message sending (continuous loop)
    global leader_id, connected_sockets, acks_received, client_id

    # ADDITION: simple request counter
    req_num = 0
    while True:
        if len(connected_sockets) == 0:
            time.sleep(5)
            continue

        message = f"C{client_id}: request{req_num} --> Hello!"
        start_time = time.time()

        if passive:
            print(f"{YELLOW} leader: {leader_id} {RESET}")
            curr_socket = connected_sockets.get(leader_id, None)
            try:
                if curr_socket:
                    curr_socket.sendall(message.encode())
                    print(f"{BLUE}[{ts()}] Client {client_id}: Sending {message} to leader {leader_id}{RESET}")
            except Exception as e:
                print(f"Failed to send message to server {leader_id}")
                curr_socket.close()
                del connected_sockets[leader_id]
        else:
            # sending to the three servers...
            for curr_server, curr_socket  in connected_sockets.items():
                try:
                    curr_socket.sendall(message.encode())
                    print(f"{BLUE}[{ts()}] Client {client_id}: Sending {message}{RESET}")
                except Exception as e:
                    print(f"Failed to send message to server {curr_server}")
                    curr_socket.close()
                    del connected_sockets[curr_server]

        # receive ACKs from three servers... ;-;
        while time.time() - start_time < 20: #20 second timeout for any request - stop waiting for ACKs
            if len(acks_received) >= 1:
                print(f"{GREEN}[{ts()}] Received response from at least one server for request{req_num}{RESET}")
                acks_received.clear()
                break
            
            time.sleep(5)
        req_num += 1


def main():
    # create TCP socket
    parser = argparse.ArgumentParser(description="Client")
    parser.add_argument("-i", "--id", type=int, default=1)
    parser.add_argument("-p", "--passive", type=bool, default=False)

    args = parser.parse_args()
    global client_id
    client_id = args.id
    global passive
    passive = args.passive
    

    global servers
    global leader_id
    global connected_sockets

    threading.Thread(target=connect_to_servers).start()
    threading.Thread(target=send_requests, args=(passive,)).start()

main()