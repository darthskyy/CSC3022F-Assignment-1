import os
import threading
from socket import *
import serv_utils
CURRENT_USERS = {}


def main () : 

    # gets the port on which to start the server on then listens for connections
    print("Starting...")
    serverPort = 50000
    x = (input("Enter the port number (leave blank to use default 50000):\n"))
    if x:
        serverPort = int(x)
    
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((gethostbyname(gethostname()),serverPort))
    print(gethostbyname(gethostname()))
    serverSocket.listen(1)
    print("The server is ready to connect.\n")
    

    # starts a thread to handle multiple clients connecting on different threads
    cThread = threading.Thread(target=threading_clients, daemon=True, args=[serverSocket])
    cThread.start()

    # on the main threads it waits for the exit command to close the server
    while True:
        admin_cmd = input("Enter 'exit()' to close the server")
        if admin_cmd == "exit()":
            print("Closing server now.")
            serverSocket.close()
            print(serverSocket)
            return

def threading_clients(serverSocket):
    # keeps waiting for clients to establish connections.
    while True:
        # the socket tries to accept a connection but breaks the loop if the server socket closes
        try:
            connectSocket, addr = serverSocket.accept()
        except Exception as e:
            print("Socket has been closed")
            break
        cThread = threading.Thread(target=file_handling, args=(connectSocket, addr))
        cThread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}\n")

def file_handling(conn, addr):
    # this is the main function for each individual client to connect
    # try block catches a ConnectionError in which a client unexpectedly ends connection
    try:
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
            for i in range(1,4):
                # the first message from the client should be a login message

                # should receive msg like LOGIN\tusername\tpassword\tlog
                recv_msg = conn.recv(1024).decode()
                recv_args = recv_msg.split("\t")

                # if the message received is not a login 
                # every implementation of a client must try to login after handshaking
                if recv_args[0] != "LOGIN":
                    send_msg = "ERROR\tUser must login first"
                    conn.send(send_msg.encode())
                else:
                    username, password, log = str(recv_args[1]), str(recv_args[2]), str(recv_args[3])
                    print(f"{log}")
                    response = serv_utils.login(username, password)
                    loggedIn = response[0]
                    send = response[1] + "\t" + response[2]
                    conn.send(send.encode())
                    if loggedIn:
                        # there is a dictionary of current users and the addresses they are logged in from
                        isAdmin = (response[2] == "ADMIN")
                        if username in CURRENT_USERS:
                            CURRENT_USERS[username].append(addr)
                        else:
                            CURRENT_USERS[username] = [addr]
                        break
            

            # MAIN FUNCTIONALITY
            while loggedIn:
                
                # recieving the data from the client 
                # this is one of the options offered
                # VIEW DOWNLOAD UPLOAD LOGOUT
                recv_msg = str(conn.recv(1024).decode())
                data = recv_msg.split("\t")
                
                #recv_msg must be OK\tCOMMAND\tPARAMETERS
                if data[0] == "OK":
                    pass
                else:
                    #add functionality for error bounce back
                    pass

                # VIEW FUNCTIONALITY
                if data[1] == "VIEW":

                    print("View files")
                    file_request = serv_utils.viewFiles(server_data_files="serverfiles")
                    
                    # sends the file list or the error message
                    if file_request[0]:
                        send_msg = "SUCCESS\t" + file_request[1]
                    else:
                        send_msg = "FAILURE\t" + file_request[1]

                    conn.send(send_msg.encode())

                    if file_request[0]:
                        #if we've actually gotten something without a hitch
                        print(f"Successfully sent file list to {addr}")
                    else:
                        print("Error encounted acquiring file list")

                # DOWNLOAD FUNCTIONALITY
                elif data[1]=="DOWNLOAD":
                    print("Download Files")
                    #data[1] : the user file name
                    # download function now returns the filesize and -1 if the file was not found
                    filename = data[2]
                    file_request = serv_utils.check_for_file(filename)
                    
                    # if file request returns a negative, the file missing error will be cause by filesize
                    if file_request[0]:
                        # gets the password from the request and communicates with the client if there is need of a password
                        file_password = file_request[1][1]
                        if file_password:
                            conn.send(f"SUCCESS\tLOCKED\tThe file: {file_request[1][0]} is password protected".encode())
                            recv_msg = conn.recv(1024).decode()
                            recv_args = recv_msg.split("\t")
                            if recv_args[1] == "PASSWORD":
                                if recv_args[2] != file_password:
                                    conn.send("FAILURE\tNOTAUTH\tPassword incorrect. Request terminated.".encode())
                                    continue

                    out_file_size, hashed = serv_utils.download(conn, filename)

                    # if the file was not found it just continues
                    if out_file_size != -1:
                        if not hashed:
                            print("ERROR: Opposing hash received")
                            conn.send("FAILURE\tDifferent hashes from Client and Server.".encode())
                            break
                        else:
                            conn.send("SUCCESS\tClient and Server hashes match".encode())

                        # receives a message from client detailing if the file has been received or
                        # lost in transmission
                        recv_msg = conn.recv(1024).decode()
                        recv_args = recv_msg.split("\t")

                        if(recv_args[1]=="RECEIVED"):
                            in_file_size = int(recv_args[2])
                            send_msg = "SUCCESS\t"
                            if in_file_size==out_file_size:
                                send_msg += "File was fully sent"
                                print(f"File {filename} was sent to {addr}")
                            else:
                                send_msg += "File was sent partially"
                                print(f"File {filename} was sent to {addr} partially")
                            
                            conn.send(send_msg.encode())
                        else:
                            send_msg = "FAILUTE\tFile might have been lost"
                            conn.send(send_msg.encode())

                # UPLOAD
                elif data[1] == "UPLOAD":
                    # recv_msg = conn.recv(1024).decode()
                    # uploading files onto the server
                    print("UPLOADING FILE TO THE SERVER")
                    # recieving the message from the user 
                    filename = data[2]
                    password = data[3]
                    filesize = int(data[4])

                    if (serv_utils.check_for_file(filename))[0]:
                        send_msg = f"NOTOK\tFile: {filename} already exists on server. Process ended."
                        conn.send(send_msg.encode())
                        continue
                    else:
                        send_msg = "OK\tServer ready to receive the file"
                        conn.send(send_msg.encode())

                    # expects a messages like UPLOAD\tfilename\tpassword\tfilesize
                    serv_utils.upload(conn, filename, password, filesize)
            
                elif data[1] == "LOGOUT":
                    CURRENT_USERS[username].remove(addr)
                    conn.send("SUCCESS\tLOGOUT\tUser successfully logged out".encode())
                    conn.close()
                    break

                elif data[1] == "ADMIN":
                    if isAdmin:
                        status_of_user_added, add_msg = serv_utils.add_user(data[2],data[3], eval(data[4]))
                        print(add_msg)
                        if(status_of_user_added):
                            conn.send(f"SUCCESS\t{add_msg}".encode())
                        else:
                            conn.send(f"FAILURE\t{add_msg}".encode())
                    else:
                        conn.send("FAILURE\tERROR\tTried to access admin privileges on regular account")
                        conn.close()
                        break
        
    except ConnectionError as e:
        print(e)
        return


if __name__ == "__main__":
    main()