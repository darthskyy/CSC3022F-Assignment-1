import getpass
import socket
import tqdm
import os


def print_menu(isAdmin=False):
    if isAdmin:
        print("Select a functionality to use\n1. View\n2. Download\n3. Upload\n4. Logout\n5. Settings")
    else:
        print("Select a functionality to use\n1. View\n2. Download\n3. Upload\n4. Logout")

def main():
    serverName = "127.0.1.1"
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
            send_msg = "VIEW\tall"
            clientSocket.send(send_msg.encode())
            
            # receives either an OK with file names
            # or a not okay with an error message
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            if recv_args[0] == "OK":
                print(recv_args[1])
            else:
                print(recv_args[1])

            print("\nViewing files ends here\n\n")
# DOWNLOAD FILES OPTION 
        elif user_input == "2": #download files
            filename = input("Enter the name of the file to be downloaded\n")
            send_msg = "DOWNLOAD\t"+filename
            clientSocket.send(send_msg.encode()) #implement specifying download directory

            #added stuff for progress bar and sending of all filetypes
            # this will send the size that the user must be ready to recieve 
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            # only happens if the file is password protected
            if recv_args[0] == "LOCKED":
                print(f"[SERVER]: {recv_args[1]}")
                file_password = input("Enter the password for the file: ")
                send_msg = "PASSWORD\t" + file_password
                clientSocket.send(send_msg.encode())
                recv_msg = clientSocket.recv(1024).decode()
                recv_args = recv_msg.split("\t")
                if recv_args[0] == "NOTOK":
                    print(f"[SERVER]: {recv_args[1]}")
                    continue
                
            if recv_args[0] == "TRANSMITTING":
                filesize = int(recv_args[1])
                clientSocket.send("OK".encode()) 
                bar = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024, leave=False)
                in_file = open(f"./downloads/down_{filename}", "wb")
                while True:
                    received_bytes = bar.n
                    if received_bytes >= filesize:
                        in_file.close()
                        break

                    message = clientSocket.recv(4096) #can't tell when entire file has been downloaded
                
                    in_file.write(message)
                    bar.update(len(message))
                if(os.path.exists(f"./downloads/down_{filename}")):
                    in_file_size = os.path.getsize(f"./downloads/down_{filename}")
                    send_msg = "RECEIVED\t" + str(in_file_size)
                    clientSocket.send(send_msg.encode())
                else:
                    send_msg = "NOTRECEIVED\tFile was not received"
                    clientSocket.send(send_msg.encode())
                
                recv_msg = clientSocket.recv(1024).decode()
                recv_args = recv_msg.split("\t")
                print(f"\n[SERVER]:{recv_args[1]}")
            else:
                print(recv_args[1])

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

            # send_msg = "UPLOAD\t" + out_filename + "\t" + file_password + "\t" + file_size
            clientSocket.send(send_msg.encode())

            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            if recv_args[0] == "NOTOK":
                print(f"[SERVER]: {recv_args[1]}")
                continue
            else:
                print(f"[SERVER]: {recv_args[1]}")

            with open(file_path, "rb") as f:
                while True:
                    data = f.read()
                    if not data:
                        break

                    clientSocket.sendall(data)

            # sending the file to be uploaded to the server 
            #   clientSocket.send(data)
            message = clientSocket.recv(1024).decode().split("\t")
            cmd = message[0]
            msg = message[1]
            if(cmd=="OK"):
                print(f"{msg}")
            else:
                print(f"{msg}")


        elif user_input == "4":
            send_msg = "LOGOUT\tNow"
            clientSocket.send(send_msg.encode())
            
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
            
            print(f"[SERVER]: {recv_args[1]}")
            clientSocket.close()
            break
        
        elif user_input == "5" and isAdmin:
            pass
        else:
            print("Invalid input")

        #clientSocket.send(send_msg.encode())
    
    send_msg = f"Client {addr} now disconnecting"
    x = input("Press enter to exit.")

if __name__ == "__main__":
    main()
