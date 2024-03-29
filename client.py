import getpass
import hashlib
import socket
import tqdm
import os


def print_menu(isAdmin=False):
    if isAdmin:
        print("Select a functionality to use\n1. View\n2. Download\n3. Upload\n4. Logout\n5. Settings")
    else:
        print("Select a functionality to use\n1. View\n2. Download\n3. Upload\n4. Logout")

def print_admin_options():
    print("ADMIN SETTINGS\n1. Add new user\n2. Delete User\nPurge System or something else")

def main():
    serverName = socket.gethostbyname(socket.gethostname())
    serverPort = 50000
    
    # here the user logs in to a specific server over a specific port
    ip = input("Enter \"IP port\" of server. Leave blank to use \'localhost\' and port 50000\n")
    if (ip):
        serverName, serverPort = ip.split(" ")
        serverPort = int(serverPort)

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    # connection is established by this point
    addr = socket.gethostbyname(socket.gethostname())


## HANDSHAKE PROTOCOLS
    # sends a handshake protocol to establish message sending
    send_msg = "HANDSHAKE\tTesting connection."
    clientSocket.send(send_msg.encode())

    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    if recv_args[0] != "HANDSHAKE":
        print(f"SERVER: {recv_msg[1]}")
        clientSocket.close()
        return
    
    print(f"[SERVER]: {recv_args[1]}")
    

## LOG IN PROTOCOL
    loggedIn = False

    for i in range(1,4):
        username = input("Username: ")
        password = getpass.getpass(prompt="Password:")
        log = f"\tLogin attempt {i} by {addr}: u: {username} p: {password}"
        send_msg = "LOGIN\t" + username + "\t" + password + log
        clientSocket.send(send_msg.encode())

        recv_msg = clientSocket.recv(1024).decode()
        recv_args = recv_msg.split("\t")
        if recv_args[0] == "ERROR":
            print(f"{recv_args[0]}: {recv_msg[1]}")
            continue
        elif recv_args[0] == "NOTAUTH":
            print(recv_args[1])
            continue
        elif recv_args[0] == "AUTH":
            print(recv_args[1])
            isAdmin = (recv_args[2] == "ADMIN")
            loggedIn = True
            break
    

## MAIN FUNCTIONALITY
    # present the menu to client
    while loggedIn:
        print_menu(isAdmin)
        user_input = input("Enter the number of the option: \n")
        
## VIEW FILES Option
        if user_input == "1": #view files
            # sends a message to the server that it want's to view all files
            send_msg = "OK\tVIEW\tall"
            clientSocket.send(send_msg.encode())
            
            # receives either an OK with file names
            # or a not okay with an error message
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            if recv_args[0] == "SUCCESS":
                print(f"[SERVER]: {recv_args[1]}")
            else:
                print(f"[SERVER]: {recv_args[1]}")

            print("\nViewing files ends here\n\n")
# DOWNLOAD FILES OPTION 
        elif user_input == "2": #download files
            if not os.path.isdir("./downloads"): os.mkdir("./downloads")
            filename = input("Enter the name of the file to be downloaded\n")
            send_msg = "OK\tDOWNLOAD\t"+filename
            clientSocket.send(send_msg.encode()) 
            in_hash = hashlib.md5()
            # this will send the size that the user must be ready to recieve 
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            # only happens if the file is password protected
            if recv_args[1] == "LOCKED":
                print(f"[SERVER]: {recv_args[2]}")
                file_password = input("Enter the password for the file: ")
                send_msg = "OK\tPASSWORD\t" + file_password
                clientSocket.send(send_msg.encode())
                recv_msg = clientSocket.recv(1024).decode()
                recv_args = recv_msg.split("\t")
                if recv_args[0] == "FAILURE":
                    print(f"[SERVER]: {recv_args[1]}")
                    continue
                
            if recv_args[1] == "TRANSMITTING":
                filesize = int(recv_args[2])
                clientSocket.send("OK\tRECEIVING\tReady to receive".encode())
                bar = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024, leave=False)
                in_file = open(f"./downloads/down_{filename}", "wb")
                while True:
                    received_bytes = bar.n
                    if received_bytes >= filesize:
                        in_file.close()
                        break

                    message = clientSocket.recv(4096) #can't tell when entire file has been downloaded
                    in_hash.update(message)
                    in_file.write(message)
                    bar.update(len(message))
                
                clientSocket.send(in_hash.hexdigest().encode())

                recv_msg = clientSocket.recv(1024).decode()
                recv_args = recv_msg.split("\t")
                if recv_args[0] == "SUCCESS":
                    print(f"[SERVER]: {recv_args[1]}")
                    if(os.path.exists(f"./downloads/down_{filename}")):
                        in_file_size = os.path.getsize(f"./downloads/down_{filename}")
                        send_msg = "OK\tRECEIVED\t" + str(in_file_size)
                        clientSocket.send(send_msg.encode())
                    else:
                        send_msg = "NOTOK\tNOTRECEIVED\tFile was not received"
                        clientSocket.send(send_msg.encode())
                    
                    recv_msg = clientSocket.recv(1024).decode()
                    recv_args = recv_msg.split("\t")
                    print(f"\n[SERVER]: {recv_args[1]}")
                else:
                    print("File invalid.")
            else:
                print(recv_args[2])

# UPLOADS
        elif user_input == "3":
            fileExists = False
            while not fileExists:
                filedirectory= input("Specify the file directory: ")
                filedirectory = "." if not filedirectory else filedirectory
                filename = input("Specify the file name: ")
                file_path = f"{filedirectory}/{filename}"
                fileExists = os.path.isfile(file_path)
                if not fileExists:
                    print(f"File with path '{file_path}' does not exist")
                    print("Try again")
                else:
                    print(f"File '{file_path}' found")

            file_size = str(os.path.getsize(file_path))
            out_filename = input("Enter the name you want to save it as on the server: ")
            file_password = input("Enter the password for the file (nothing if it's to be open): ")

            send_msg = "OK\tUPLOAD\t" + out_filename + "\t" + file_password + "\t" + file_size
            clientSocket.send(send_msg.encode())

            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            if recv_args[0] == "NOTOK":
                print(f"[SERVER]: {recv_args[1]}")
                continue
            else:
                print(f"[SERVER]: {recv_args[1]}")
            out_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(4096) #limit size being sent at once
                    if not data:
                        break
                    out_hash.update(data)
                    clientSocket.sendall(data)
            f.close()
            # sending the file to be uploaded to the server 
            #   clientSocket.send(data)
            # in_hash = clientSocket.recv(1024).decode()
            # hashed = (in_hash == out_hash.hexdigest())
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            out_filesize = str(recv_args[1])
            if (file_size == out_filesize): print("Files are equal size")
            else: print("Files are not equal size")

            clientSocket.send(out_hash.hexdigest().encode())
            message = clientSocket.recv(1024).decode().split("\t")
            cmd = message[0]
            msg = message[1]
            
            """
            if(cmd=="OK"):
                print(f"{msg}")
            else:
            """
            print(f"{msg}")

        elif user_input == "4":
            send_msg = "OK\tLOGOUT\tNow"
            clientSocket.send(send_msg.encode())
            
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            
            print(f"[SERVER]: {recv_args[2]}")
            clientSocket.close()
            print("Logging out now.")
            break
    
        #ADMIN USER
        elif user_input == "5" and isAdmin:
            print_admin_options()
            option = input("Enter the number of the option you want:")

            print("Now adding a new user to the server")

            send_msg = "OK\tADMIN"
            user_type_option = ""
            while user_type_option!="1" and user_type_option!="2":
                user_type_option = input("What type of account would you like it to be\n[1]Admin or [2]REGULAR: ")
            
            user_admin = "True" if user_type_option=="1" else "False"

            username = input("Enter the username: ")
            password = input("Enter the password:")
            password_conformation = input("Confirm the password entered: ")
            while(password != password_conformation):
                print("The passwords do not match.")
                password = input("Enter the password:")
                password_conformation = input("Confirm the password entered: ")

            send_msg = send_msg + f"\t{username}\t{password}\t{user_admin}"
            clientSocket.send(send_msg.encode())
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            if(recv_args[0]=="SUCCESS"):
                print(recv_args[1])
            else:
                print(recv_args[1])
        else:
            print("Invalid input")
            
            
            


if __name__ == "__main__":
    try:
        main()
    except ConnectionError as e:
        print(e)
        print("Forcefully disconnect from the server.")
