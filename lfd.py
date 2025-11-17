import socket
import time
import argparse
import threading

from datetime import datetime
GREEN = "\033[92m"   # successful heartbeat
RED = "\033[91m"     # failure or timeout
YELLOW = "\033[93m"  # reconnect attempt
BLUE = "\033[94m"    # server ack
RESET = "\033[0m"
CYAN = "\033[96m"


def ts():
    return datetime.now().strftime("%H:%M:%S")

HOST = "127.0.0.1" #change to server ip
PORT = 65080
TIMEOUT = 10

GFD_HOST = "127.0.0.1" #change to server ip
GFD_PORT = 65084    

current_leader = 0

heartbeat_interval = 10
# updated_leader = False


gfd_connected = False
gfd_sock = None
connected = False

def handle_gfd():
    # connecting to gfd
    global gfd_connected, gfd_sock
    # Try connecting to GFD, but do not crash if unavailable

    while not gfd_connected:
        try:
            gfd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            gfd_sock.settimeout(TIMEOUT)
            gfd_sock.connect((GFD_HOST, GFD_PORT))
            gfd_connected = True
            print(f"[{ts()}] LFD{id}: connected to GFD at {GFD_HOST}:{GFD_PORT}")

        except Exception as e:
            pass
            # print(f"{YELLOW}[{ts()}] LFD{id}: GFD not available yet ({e}); will retry...{RESET}")
    # gfd, gfd_connected = connection(host=GFD_HOST, port=GFD_PORT)

    while True:
        if gfd_connected: #heartbeats for the gfd
            # if first_connect:
            #     first_connect = 0
                # gfd_sock.sendall(f"LFD{id}: Connected \n".encode())
            # else:
            try:
                gfd_sock.sendall(f"LFD{id}: Heartbeat \n".encode())
                gfd_sock.settimeout(TIMEOUT)
                print(f"Sending heartbeat at {int(time.time())}")
                try:
                    resp = gfd_sock.recv(1024).decode()
                    if "ACK" in resp:
                        print(f"{BLUE}[{ts()}] LFD{id}: ACK received from GFD{RESET}")
                    if "New Leader" in resp:
                        current_leader = resp.split("New Leader: ")[1].strip()
                        print(f"{CYAN}[{ts()}] LFD{id}: New Leader: {current_leader}{RESET}")
                        
                except socket.timeout:
                    print(f"{RED}[{ts()}] LFD{id}: No ACK (timeout={TIMEOUT}s) GFD may have failed{RESET}")
                    gfd_connected = False
                    gfd_sock.close()
                time.sleep(heartbeat_interval)
            except socket.timeout:
                print("Timeout exceeded, GFD failed")
            except socket.error as e:
                # print(f"{RED}[{ts()}] Error sending heartbeat: {e}")
                print(f"{RED}[{ts()}] LFD{id}: GFD died")
                gfd_connected = False
                gfd_sock.close()
                


def handle_server():
    s = None
    global connected
    global gfd_sock
    global current_leader

    while not connected:
        try:
            s, connected = connection()
            if connected:
                print(f"{GREEN}[{ts()}] LFD{id}: Connected to server at {HOST}:{PORT+id}{RESET}")
                gfd_sock.sendall(f"LFD{id}: Server Connected".encode())
        except Exception as e:
            print(f"{YELLOW}[{ts()}] LFD{id}: Server not available yet ({e}); will retry...{RESET}")
        time.sleep(2)

    while True:
        if connected: #heartbeats for the server
            try: 
                s.sendall("Heartbeat".encode())
                print(f"Sending heartbeat at {int(time.time())}")
                # ADDITION: LFD (inside heartbeat loop)
                print(f"{GREEN}[{ts()}] LFD{id}: sending heartbeat to S{id}{RESET}")

                # send message to server upon new leader?
                msg = f"GFD: New Leader: {current_leader}"
                s.sendall(msg.encode())

                # ADDITION: wait briefly for ACK to confirm server alive
                s.settimeout(TIMEOUT)
                try:
                    resp = s.recv(3).decode()
                    print(f"Received response: {resp}")
                    if "ACK" in resp:
                        print(f"{BLUE}[{ts()}] LFD{id}: ACK received from server{RESET}")

                except socket.timeout:
                    print(f"{RED}[{ts()}] LFD{id}: No ACK (timeout={TIMEOUT}s) server may have failed{RESET}")
                    connected = False
                    s.close()

            except socket.timeout:
                print("Timeout exceeded, server failed")
            except socket.error as e:
                print(f"Error sending heartbeat")
                print(f"{RED}[{ts()}] LFD{id}: Server {id} died")
                connected = False
                s.close()
                gfd_sock.sendall(f"LFD{id}: Server Disconnected".encode())

        else:
            try:
                print(f"Trying to reconnect")
                # ADDITION: colorize reconnect attempts
                print(f"{YELLOW}[{ts()}] LFD{id}: Attempting reconnect to {HOST}:{PORT+id}{RESET}")
                s, connected = connection()
                if connected:
                    print(f"Connected to server at", HOST)
                    gfd_sock.sendall(f"LFD{id}: Server Connected".encode())
            except socket.error as e:
                pass
        time.sleep(heartbeat_interval)


def main():
    data = ""
    parser = argparse.ArgumentParser(description="Heartbeat")
    parser.add_argument("-f", "--freq", type=int, default=5)
    parser.add_argument("-t", "--timeout", type=int, default=5)
    parser.add_argument("-i", "--id", type=int, default=1)
    parser.add_argument("--gfd_host", type=str, default=GFD_HOST)
    parser.add_argument("--gfd_port", type=int, default=GFD_PORT)

    args = parser.parse_args()
    global heartbeat_interval
    heartbeat_interval = args.freq
    global id, current_leader
    id = args.id
    TIMEOUT = args.timeout

    threading.Thread(target=handle_gfd).start()
    threading.Thread(target=handle_server).start()


def connection(host=HOST, port=PORT, timeout=TIMEOUT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if hasattr(socket, 'SO_REUSEPORT'):
            # Set SO_REUSEPORT to 1 (or True) to enable it
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:
            # Fallback to SO_REUSEADDR for older systems or certain platforms
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        print("port:", PORT+id)
        s.connect((HOST, PORT+id))
        print("!!!!!!!!!!!!!!!!")
        s.settimeout(TIMEOUT) 
        # print(f"Connected to server at", HOST)
        connected = True
    except Exception as e:
        print(f"Cannot connect to the server {e}")
        connected = False
    return s, connected


main()