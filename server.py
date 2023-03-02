import os
import threading
from socket import *
import serv_utils
CURRENT_USERS = []


def main () : 

    print("Starting...")
    serverPort = 50000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((gethostbyname(gethostname()),serverPort))
    serverSocket.listen(1)
    print("The server is ready to connect.\n")
    
    while True:
        connectSocket, addr = serverSocket.accept()
        cThread = threading.Thread(target=file_handling, args=(connectSocket, addr))
        cThread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}\n")

def file_handling(conn, addr):
    with conn:
        print(f"Connected by {addr}")

## HANDSHAKE PROTOCOL
        # receives handshaking protocol and sends back handshake protocol if everything is okay
        recv_msg = conn.recv(1024).decode()
        recv_args = recv_msg.split("\t")
        # if not handshaked properly the connection ends there and then
        if recv_args[0] != "HANDSHAKE":
            conn.send("ERROR\tHandshake protocol not obeyed; ending connection".encode())
            conn.close()
            return
        
        print(f"{addr}: {recv_args[1]}")
        send_msg = "HANDSHAKE\tConnection established securely."
        conn.send(send_msg.encode())


## LOG IN PROTOCOL
        loggedIn = False
        #logging in
        # should receive msg like LOGIN\tusername\tpassword
        for i in range(1,4):
            # the first message from the client should be a login message
            recv_msg = conn.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            # if the message received is not a login 
            if recv_args[0] != "LOGIN":
                send_msg = "ERROR\tUser must login first"
                conn.send(send_msg.encode())
            else:
                username, password, log = str(recv_args[1]), str(recv_args[2]), str(recv_args[3])
                print(log)
                response = serv_utils.login(username, password)
                loggedIn = response[0]
                conn.send(response[1].encode())
                if loggedIn:
                    CURRENT_USERS.append(username)
                    break
        

# MAIN FUNCTIONALITY
        while loggedIn:
            
            # recieving the data from the client 
            # this is one of the options offered
            # VIEW DOWNLOAD UPLOAD LOGOUT
            data = str(conn.recv(1024).decode())
            data = data.split("\t")

            if data[0] == "VIEW":
                print("View files")
                file_request = serv_utils.viewFiles(server_data_files="serverfiles")
                
                # sends the file list or the error message
                send_msg = file_request[1]
                conn.send(send_msg.encode())

                if file_request[0]:
                    #if we've actually gotten something without a hitch
                    print(f"Successfully sent file list to {addr}")
                else:
                    print("Error encounted acquiring file list")
            
            elif data[0]=="DOWNLOAD":
                print("Download Files")
                #data[1] : the user file name
                # download function now returns the filesize and -1 if the file was not found
                out_file_size, hashed = serv_utils.download(conn,data[1])

                # if the file was not found it just continues
                if out_file_size != -1:
                    if not hashed:
                        print("ERROR: Different hash")
                        conn.send("NOTOK".encode())
                    
                    else:
                        conn.send("OK".encode())
                    recv_msg = conn.recv(1024).decode()
                    recv_args = recv_msg.split("\t")

                    if(recv_args[0]=="RECEIVED"):
                        in_file_size = int(recv_args[1])
                        send_msg = "OK\t"
                        if in_file_size==out_file_size:
                            send_msg += "File was fully sent"
                            print(f"File {data[1]} was sent to {addr}")
                        else:
                            send_msg += "File was sent partially"
                            print(f"File {data[1]} was sent to {addr} partially")
                        
                        conn.send(send_msg.encode())
                    else:
                        send_msg = "NOTOK\tFile might have been lost"
                        conn.send(send_msg.encode())

            elif data[0] == "UPLOAD":
                # recv_msg = conn.recv(1024).decode()
                # uploading files onto the server
                print("UPLOADING FILE TO THE SERVER")
                # recieving the message from the user 
                conn.send("Uploading file to the server".encode())
                serv_utils.upload(conn,filename=data[2],filesize=int(data[3]))
            
            else:
                pass


if __name__ == "__main__":
    main()