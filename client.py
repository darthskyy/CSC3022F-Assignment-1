import getpass
import hashlib
import socket
import tqdm
import os


def print_menu():
    print("Select a functionality to use\n1. View\n2. Download\n3. Upload")

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
            loggedIn = True
            break
    

## MAIN FUNCTIONALITY
    # present the menu to client
    while loggedIn:
        print_menu()
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
            in_hash = hashlib.sha256()
            # this will send the size that the user must be ready to recieve 
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")
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
                    in_hash.update(message)
                    in_file.write(message)
                    bar.update(len(message))
                print(f"\n\nhash is : {in_hash.hexdigest()}")
                clientSocket.send(in_hash.hexdigest().encode())
                #get hash state back
                hash_state:str = clientSocket.recv(1024).decode()
                if (hash_state == "OK"):
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
                    print("File error. Try to redownload")
            else:
                print(recv_args[1])


        elif user_input == "3":
          send_msg = "UPLOAD\t"
          filedirectory= input("Specify the file directory: ")
          send_msg += filedirectory +"\t"
          filename = input("Specify the file name: ")
          send_msg += filename +"\t"
          directory = os.path.dirname(filedirectory)
        #   full_path = os.path.join(directory,filename)
          full_path = f"./{filedirectory}/{filename}"
          send_msg += str(os.path.getsize(full_path)) +"\t"
          clientSocket.send(send_msg.encode())
        #   clientSocket.send(send_msg.encode())0
          print(clientSocket.recv(1024).decode())

          with open(full_path, "rb") as f:
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



        elif user_input == 4:
            print("Log Out")
        else:
            print("Invalid input")

        #clientSocket.send(send_msg.encode())
    
    send_msg = f"Client {addr} now disconnecting"
    x = input("Press enter to exit.")
    clientSocket.send(send_msg.encode())
    clientSocket.close()

if __name__ == "__main__":
    main()
