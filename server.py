import socket
import threading

# here is the StackOverflow I'm referencing:
# https://stackoverflow.com/questions/10810249/python-socket-multiple-clients

# whoever is hosting: do the following -->
# in terminal: ipconfig (windows) or ifconfig (mac)
# paste it into "host"

HOST = "172.26.42.163"
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
                    continue
            
            with state_lock:
                my_state += 1
                current_state = my_state
            print(f"Server state before reply: {current_state}")

            # echo data back 
            reply = f"Message received. Server state: {current_state}"
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # bind socket to host and port
        s.bind((HOST, PORT))
        # listen for connections
        s.listen()

        # accept connections in a loop
        while True:
            conn, addr = s.accept()
            print(f"Connected to client")
            threading.Thread(target=new_client, args=(conn, addr)).start()

main()