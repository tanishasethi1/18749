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

def print_membership():
    # message format:
    # RM: x members - S1, S2, ...
    members = ""
    for lfd_id in membership.keys():
        members += f"S{lfd_id}, "

# talk to GFD
def handle_gfd(conn, addr):
    # handle updates
    member_count = 0
    members_list = None
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            # data in format: "GFD: {membership} members - S1, S2, ..."
            print("data :", data)
            membership = data.split("-")[1].strip()
            members_list = membership.split(", ")
            print(members_list)

    except Exception as e:
        print(f"Error handling RM {addr}: {e}")
            
    return 


def main():
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

