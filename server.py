import os
import threading
import sys
from socket import *
from hashlib import md5
from tqdm import tqdm
#from . import serv_utils

FORMAT = "utf-8"
server_data_files = "serverfiles"
serverPort = 4000

def md5sum(filename):
    hash = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
            hash.update(chunk)
    return hash.hexdigest()

def file_handling (connection, addr):
    # Send the starting message from the server to the user
    connection.send("OK@Welcome to the File Sever.\n Enter your Username and Password seperated by a space:".encode(FORMAT))
    # this part will detect if the user is in the server

    ##TODO: Enter the logic of the user file login name --> Simba 

    message = connection.recv(1024).decode(FORMAT)
    message =  message.split("\n")
    print(message[0])
    
    proceed = "OK" # I just used this to see if the user can proceed

    # data send to the user 

    if(proceed =="OK"):
        data = "OK@"
        data += "1: List all the files from the server.\n"
        data += "2 <path>: Upload a file to the server.\n"
        data += "3 <filename>: Delete a file from the server.\n"
        data += "4 <filename>: Download a file from the server.\n"
        data += "LOGOUT: Disconnect from the server.\n"
        data += "HELP: List all the commands."

        connection.send(data.encode(FORMAT))

        while True:
            data = connection.recv(1024).decode(FORMAT)
            data =  data.split("@")
            command = data[0]

            if command == "1":
                # view files from the serv_utils directory
                print("View Files")
            elif command == "2":
                # upload the files specified into the directory
                name,text, permissions= data[1],data[2], data[3]# the name of the file and the context of the 
                #upload(sock,name,text,size)
                print("Uploading")  
            if command == "3":
                # delete(sock,server_data_files,filename)
                print("Deleting the files")
            if command =="4":
                print("Downloading files")
             
            connection.close()

def main () : 
    print("Starting...")
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((gethostbyname(gethostname()),serverPort))
    serverSocket.listen(1)
    print("The server is ready to connect.\n")
    while True:
        connectSocket, addr = serverSocket.accept()
        cThread = threading.Thread(target=file_handling, args=(connectSocket, addr))
        cThread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        #add code to shutdown server. running in

if __name__ == "__main__":
    main()