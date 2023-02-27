from socket import *

IP = gethostbyname(gethostname())
PORT = 4000
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

def main():
    client = socket(AF_INET, SOCK_STREAM)
    client.connect(ADDR) # create a connection with the server 

    while True:
        server_message = client.recv(SIZE).decode(FORMAT) # recieve the data from the server
        cmd, msg = server_message.split("@")
    
        # # break of the server was not connected at the time 
        if cmd == "DISCONNECTED":
            print(f"[SERVER]: {msg}")
            break
        elif cmd == "OK": # testing the state of the server 
            print(f"{msg}")

        # taking in the user input 
        data = input("> ")
        data = data.split(" ")
        username = data[0]
        password = data[1]
        client_login = username +"\n"+password
        client.send(client_login.encode(FORMAT))


        # get the users input for the commands again 

        data = input("> ")
        data = data.split(" ")
        cmd = data[0]
        client_login = username +"\n"+password
        client.send(client_login.encode(FORMAT))
        #not sure why we're checking cmd. thought we would be checking data (user input)
      
        if cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break
        elif cmd == "LIST":
            client.send(cmd.encode(FORMAT))
        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
        elif cmd == "UPLOAD":
            path = data[1]
            permissions = data[2]

            with open(f"{path}", "r") as f:
                text = f.read()

            filename = path.split("/")[-1]
            send_data = f"{cmd}@{filename}@{text}@{permissions}"
            client.send(send_data.encode(FORMAT))
        elif cmd == "DOWNLOAD":
            #implement client side downloading
            print("Downloading")

    print("Disconnected from the server.")
    client.close()

if __name__ == "__main__":
    main()
