import socket
import threading
import time
from datetime import datetime
import argparse
import os
import subprocess

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
members_list = {}

current_leader = 0


def relaunch_server(server_id, passive):
    print(f"{YELLOW}[{ts()}] RM: Relaunching Server {server_id}{RESET}")
    current_directory = os.getcwd()

    if passive:
        cmd = f"python3 {current_directory}/server.py -i {server_id} -p"
    else:
        cmd = f"python3 {current_directory}/server.py -i {server_id} --recover --primary {current_leader}"
    
    subprocess.Popen([
        "osascript", "-e",
        f'tell application "Terminal" to do script "{cmd}"'
    ])
        
    print(f"{GREEN}[{ts()}] RM: Server {server_id} relaunched successfully.{RESET}")

# talk to GFD
def handle_gfd(conn, addr):
    # handle updates
    global member_count, members_list, current_leader
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            # data in format: "GFD: {membership} members - Server added = {new/disconnected serverID }."
            print(data)
            new_member_id = data.split("=")[1].strip()
            if "Server added" in data:
                if new_member_id not in members_list.keys():
                    members_list[new_member_id] = True
                    member_count += 1
                    print(f"{BLUE} [{ts()}] RM: Server {new_member_id} added to membership list. Total members: {member_count}{RESET}")
                if current_leader == 0:
                    current_leader = new_member_id
                    if passive:
                        print(f"{GREEN}[{ts()}] RM: New leader is Server {current_leader}{RESET}") #send message to gfd?
                    message = f"RM: New Leader: {current_leader}"
                    conn.sendall(message.encode())
            if "Server disconnected" in data:
                if new_member_id in members_list.keys():
                    members_list.pop(new_member_id)
                    member_count -= 1
                    print(f"{BLUE} [{ts()}] RM: Server {new_member_id} removed from membership. Total members: {member_count}{RESET}")
                    threading.Thread(target=relaunch_server, args=(new_member_id, passive)).start()
                if new_member_id == current_leader: #re-elect leader to first server in the list
                    if len(members_list) > 0:
                        current_leader = next(iter(members_list))
                        if passive:
                            print(f"{GREEN}[{ts()}] RM: New leader is Server {current_leader}{RESET}") #send message to gfd?
                        message = f"RM: New Leader: {current_leader}"
                        conn.sendall(message.encode())
                    else:
                        current_leader = 0

            if passive:
                print(f"{YELLOW}[{ts()}] RM: Current leader: {current_leader}{RESET}")
            # print members list
            ml = ""
            for i in members_list.keys():
                ml += str(i) + " "
            print(f"{GREEN}[{ts()}] Members List: {ml}{RESET}")

    except Exception as e:
        print(f"Error handling RM {addr}: {e}")
            
    return 


def main():
    parser = argparse.ArgumentParser(description="Server")
    parser.add_argument("-p", "--passive", action='store_true', help="Run server in passive mode")
    args = parser.parse_args()
    global passive
    passive = args.passive
    # connect to GFD   
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"RM listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            threading.Thread(target=handle_gfd, args=(conn, addr)).start()
            
main()

