import os, platform, time
# tries to install all the required modules
try:
    os.system("pip install -r requirements.txt")
except:
    print("Failed to install prerequisites")
    time.sleep(1)
finally:
    if platform.system() == "Windows":
        os.system("cls")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        os.system("clear") 

import threading
from socket import *
from serv_utils import log_activity
import serv_utils
import time
CURRENT_USERS = {}


def main () :
    # gets the port on which to start the server on then listens for connections
    log_activity("Starting Session...")
    if not os.path.exists("filekey.key"):
        log_activity("No key found. Generating...")
        serv_utils.make_key()
    log_activity("Encryption key found")
    # creates serverfiles directory if it is non-existent
    if not os.path.isdir("./serverfiles"): os.mkdir("./serverfiles")

    
    serverPort = 50000
    x = (input("Enter the port number (leave blank to use default 50000):\n"))
    if x:
        try:
            serverPort = int(x)
        except:
            print("Error: serverPort defaulted to 50000")
    

    # connects the socket
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((gethostbyname(gethostname()),serverPort))
    serverSocket.listen(1)
    log_activity(f"The server: {gethostbyname(gethostname())} is ready to connect.\n")
    

    # starts a thread to handle multiple clients connecting on different threads
    cThread = threading.Thread(target=threading_clients, daemon=True, args=[serverSocket])
    cThread.start()

    # on the main threads it waits for the exit command to close the server
    while True:
        admin_cmd = input("Enter 'exit()' to close the server\n")
        if admin_cmd == "exit()":
            log_activity("Closing server session.")
            serverSocket.close()
            log_activity(serverSocket)
            return

def threading_clients(serverSocket):
    # keeps waiting for clients to establish connections.
    while True:
        # the socket tries to accept a connection but breaks the loop if the server socket closes
        try:
            connectSocket, addr = serverSocket.accept()
        except Exception as e:
            log_activity("Socket has been closed")
            break
        cThread = threading.Thread(target=file_handling, args=(connectSocket, addr))
        cThread.start()
        log_activity(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}\n")

def file_handling(conn, addr):
    # this is the main function for each individual client to connect
    # try block catches a ConnectionError in which a client unexpectedly ends connection
    try:
        with conn:
            log_activity(f"Connected by {addr}")

            ## HANDSHAKE PROTOCOL
            # receives handshaking protocol and sends back handshake protocol if everything is okay
            recv_msg = conn.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            # if not handshaked properly the connection ends there and then
            if recv_args[0] != "HANDSHAKE":
                conn.send("ERROR\tHandshake protocol not obeyed; ending connection".encode())
                conn.close()
                return
            
            log_activity(f"{addr}: {recv_args[1]}")
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
                    log = f"Login attempt {i} by {addr} with {username} || {password}"
                    log_activity(f"{log}")
                    response = serv_utils.login(username, password)
                    loggedIn = response[0]
                    send = response[1] + "\t" + response[2]
                    conn.send(send.encode())
                    if loggedIn:
                        # there is a dictionary of current users and the addresses they are logged in from
                        isAdmin = (response[2] == "ADMIN")
                        log_activity(f"{addr} successfully logged in as {response[2]}")
                        if username in CURRENT_USERS:
                            CURRENT_USERS[username].append(addr)
                        else:
                            CURRENT_USERS[username] = [addr]
                        break
                    else:
                        # if the user fails to login, the loop continues
                        reason = response[1].split('\t')[1]
                        log_activity(f"Login attempt {i} by {addr} failed. Reason: {reason}.")
                        continue
            

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
                    log_activity("Message error")
                    break

                # VIEW FUNCTIONALITY
                if data[1] == "VIEW":

                    log_activity(f"{addr} requesting file list")
                    # gets a string representation of all the files in the system and transmits it
                    file_request = serv_utils.viewFiles(server_data_files="serverfiles")
                    
                    # sends the file list or the error message
                    if file_request[0]:
                        send_msg = "SUCCESS\t" + file_request[1]
                    else:
                        send_msg = "FAILURE\t" + file_request[1]

                    conn.send(send_msg.encode())

                    # confirms if the file was actually sent to the client
                    if file_request[0]:
                        #if we've actually gotten something without a hitch
                        log_activity(f"Successfully sent file list to {addr}")
                    else:
                        log_activity("Error encounted acquiring file list")

                # DOWNLOAD FUNCTIONALITY
                elif data[1]=="DOWNLOAD":
                    #data[1] : the user file name
                    # download function now returns the filesize and -1 if the file was not found
                    filename = data[2]
                    file_request = serv_utils.check_for_file(filename)
                    log_activity(f"{addr} requesting file download of '{filename}'")
                    
                    # if file request returns a negative, the file missing error will be cause by filesize
                    if file_request[0]:
                        # gets the password from the request and communicates with the client if there is need of a password
                        file_password = file_request[1][1]
                        # if the file_password is empty the selection won't pass
                        if file_password:
                            # sends a request for the password and handles the receipt from the client
                            conn.send(f"SUCCESS\tLOCKED\tThe file: {file_request[1][0]} is password protected".encode())
                            log_activity(f"Sending {addr} password request for '{filename}'")
                            recv_msg = conn.recv(1024).decode()
                            recv_args = recv_msg.split("\t")
                            if recv_args[1] == "PASSWORD":
                                if recv_args[2] != file_password:
                                    conn.send("FAILURE\tNOTAUTH\tPassword incorrect. Request terminated.".encode())
                                    log_activity(f"{addr} password incorrect for '{filename}'. Operation cancelled.")
                                    continue
                                else:
                                    log_activity(f"{addr} password accepted for '{filename}'.")
                    
                    # sends the file to the client using the download function
                    # gets the file size and the hashkey for the file in return
                    out_file_size, hashed = serv_utils.download(conn, filename)

                    # if the file was not found it just continues
                    if out_file_size != -1:
                        if not hashed:
                            log_activity("ERROR: Opposing hash received from client: {addr}.")
                            conn.send("FAILURE\tDifferent hashes from Client and Server.".encode())
                            break
                        else:
                            log_activity(f"Hash from client: {addr} matches.")
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
                                log_activity(f"File {filename} was sent to {addr}")
                            else:
                                send_msg += "File was sent partially"
                                log_activity(f"File {filename} was sent to {addr} partially")
                            
                            conn.send(send_msg.encode())
                        else:
                            log_activity(f"File {filename} transfer to {addr} failed. Reason: File lost in transmission.")
                            send_msg = "FAILUTE\tFile might have been lost"
                            conn.send(send_msg.encode())

                # UPLOAD
                elif data[1] == "UPLOAD":
                    # recv_msg = conn.recv(1024).decode()
                    # uploading files onto the server
                    # recieving the message from the user 
                    filename = data[2]
                    password = data[3]
                    filesize = int(data[4])
                    log_activity(f"{addr} requesting file upload of '{filename}' to server")

                    # if the file that the client is uploading has an identical name to a file in serverfiles
                    # the upload is blocked
                    if (serv_utils.check_for_file(filename))[0]:
                        send_msg = f"NOTOK\tFile: {filename} already exists on server. Process ended."
                        log_activity(f"{addr} file upload of '{filename}' blocked by server. Reason: File already exists.")
                        conn.send(send_msg.encode())
                        continue
                    else:
                        send_msg = "OK\tServer ready to receive the file"
                        log_activity(f"{addr} file upload request of '{filename}' accepted by server. Ready to receive file.")
                        conn.send(send_msg.encode())

                    # expects a messages like UPLOAD\tfilename\tpassword\tfilesize
                    serv_utils.upload(conn, filename, password, filesize)
            
                elif data[1] == "LOGOUT":
                    CURRENT_USERS[username].remove(addr)
                    conn.send("SUCCESS\tLOGOUT\tUser successfully logged out".encode())
                    log_activity(f"{addr} logged out from current session.")
                    conn.close()
                    break

                elif data[1] == "ADMIN":
                    # the only admin feature so far is the addition of a user
                    if isAdmin:
                        status_of_user_added, add_msg = serv_utils.add_user(data[2],data[3], eval(data[4]))
                        allocation_status = serv_utils
                        log_activity(add_msg)
                        if(status_of_user_added):
                            conn.send(f"SUCCESS\t{add_msg}".encode())
                        else:
                            conn.send(f"FAILURE\t{add_msg}".encode())
                    else:
                        conn.send("FAILURE\tERROR\tTried to access admin privileges on regular account")
                        log_activity(f"POSSIBLE RISK: {addr} tried to access admin privileges on regular account")
                        conn.close()
                        break
        
    except Exception as e:
        print(e)
        return


if __name__ == "__main__":
    main()