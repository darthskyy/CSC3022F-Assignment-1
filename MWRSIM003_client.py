import os, platform
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

# imports them after they are installed
import getpass
import hashlib
import socket
import tqdm
import time
import math
import sys

OS = platform.system()
def clear_ui(sleep_time=0):
    # clears the user interface after a certain number of seconds
    time.sleep(sleep_time)
    if OS=="Windows":
        os.system("cls")
    else:
        os.system("clear")

def print_menu(isAdmin=False):
    # this methods prints the appropriate menu for the type of user
    if isAdmin:
        print("Select a functionality to use\n\t1. View\n\t2. Download\n\t3. Upload\n\t4. Logout\n\t5. Add User(s)")
    else:
        print("Select a functionality to use\n\t1. View\n\t2. Download\n\t3. Upload\n\t4. Logout")

def print_files(file_list, current_page, files_per_page=10):
    """
    Paginates a list of files in which the entries are in the format "filename|status" and displays the current page
    """

    # gets the maximum number of pages required
    pages = math.ceil(len(file_list)/files_per_page)
    page_print = "Page "
    for i in range(1, pages+1):
        if i==current_page:
            page_print += f"[{i}] "
        else:
            page_print += str(i) + " "
    print(page_print)

    # prints out the layout in a nice style
    print(f"{'index':<10}|{'file name':<70}|{'status':<20}")
    print("="*103)
    
    start_index = (current_page-1)*files_per_page
    end_index = start_index+files_per_page
    end_index = end_index if end_index < len(file_list) else len(file_list)

    for i in range(start_index, end_index):
        items = file_list[i].split("|")
        print(f"{i+1:<10}|{items[0]:<70}|{items[1]:<20}|")
        

def dots(num):
    # prints dots for aesthetic "loading screen" reasons
    for i in range(num):
        print(".", end="", sep="")
        time.sleep(0.2)
    print()

def print_title(title: str):
    # prints a title in the middle of the screen
    txt = title.upper()
    width = os.get_terminal_size().columns
    txt = txt.center(width, "-")
    print(txt)
    print()

def request_serv_addr():
    # requests the connection info from the user
    ip = input("Enter the IP address of the server you want to connect to (or nothing to default to local):\n")
    port_num = input("Enter the port number you want to use to connect (or nothing to use 50000):\n")
    ip = ip if ip else socket.gethostbyname(socket.gethostname())
    try:
        port_num = int(port_num) if port_num else 50000
    except:
        print("Port number errorneous defaulted to 50000")
        port_num = 50000

    return ip, port_num

def check_name_validity(filename: str):
    # check that a filename entered by the user does not contain illegal characters
    # also checks to make sure the user cannot access directories within the server files
    if not filename or filename=="." or filename == "..": return False
    
    illegal_chars = ["|", "\\", "/", ":", "*", "?", "\"", "<", ">"]
    return len([i for i in illegal_chars if i in filename]) == 0



# main functions
def logout(clientSocket, username):
    # logs out the user and makes one last communication with the server before closing socket
    clear_ui()
    print("Logging out", end="")
    dots(5)
    
    send_msg = "OK\tLOGOUT\tNow"
    clientSocket.send(send_msg.encode())
    
    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    
    print(f"[SERVER]: {recv_args[2]}")
    clientSocket.close()
    print(f"{username} successfully logged out.")

def interactive_add_user(clientSocket):
    # modular code to add a user to the server using admin privileges

    send_msg = "OK\tADMIN"
    print_title("adding user")
    user_type_option = input("What type of account would you like it to be?\n[1]Admin or [2]REGULAR: ")
    
    # continues asking the user for until a valid option is chosen
    while user_type_option!="1" and user_type_option!="2":
        print("Error: invalid input")
        clear_ui(0.5)
        print_title("adding user")
        user_type_option = input("What type of account would you like it to be?\n[1]Admin or [2]REGULAR: ")
    
    user_admin = "True" if user_type_option=="1" else "False"

    # gets the account details for the account to be added
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    password_conformation = input("Confirm the password entered: ")
    while(password != password_conformation):
        print("The passwords do not match.")
        password = input("Enter the password:")
        password_conformation = input("Confirm the password entered: ")

    # sends the message to the server requesting the addition of a user and receives a response on the status
    send_msg = send_msg + f"\t{username}\t{password}\t{user_admin}"
    clientSocket.send(send_msg.encode())
    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    if(recv_args[0]=="SUCCESS"):
        clear_ui()
        print(f"User: '{username}' has been successfully added.")
    else:
        print(f"[SERVER]: {recv_args[1]}")

def interactive_download(clientSocket):
    # gives an opportunity for the user to enter name of a file and download it from the server if it is available

    # gets the file's server name and what the user would like to download it as
    # keeps checking for name validity until the user enters a valid filename
    filename = ""
    isValidName = check_name_validity(filename)
    while not isValidName:
        filename = input("Enter a (valid) name of the file to be downloaded (or nothing to return to previous):\n")
        
        # preemptively returns if the user decides not to download
        if filename == "": return
        isValidName = check_name_validity(filename)
    
    down_filename = input("Enter the name you'd like to save the file under:\n")
    isValidName = check_name_validity(down_filename)
    while not isValidName:
        down_filename = input("Enter the name you'd like to save the file under:\n")
        isValidName = check_name_validity(down_filename)
    
    # calls to the download function
    download(clientSocket, filename, down_filename)

def download(clientSocket, filename, down_filename):
    # modular code to download a file from the server an save it in the downloads folder of the client

    # firstly checks if there is a downloads directory and makes one if there isn't
    if not os.path.isdir("./downloads"): os.mkdir("./downloads")

    # sends a download request with the file name to the server
    send_msg = "OK\tDOWNLOAD\t"+filename
    clientSocket.send(send_msg.encode())

    in_hash = hashlib.md5() # this is the hash for which the server file and the download will be compared


    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")

    # only happens if the file is password protected
    if recv_args[1] == "LOCKED":
        # gets the password and sends it to the server which checks if it is correct, otherwise the interaction ends
        file_password = input("Enter the password for the file: ")
        send_msg = "OK\tPASSWORD\t" + file_password
        clientSocket.send(send_msg.encode())
        recv_msg = clientSocket.recv(1024).decode()
        recv_args = recv_msg.split("\t")
        if recv_args[0] == "FAILURE":
            print(f"Incorrect password for {filename}. Request terminated.")
            return
    
    # one the file authentication is over the server should start transmitting the file
    # the interaction is marked by the server first sending the file size
    if recv_args[1] == "TRANSMITTING":
        filesize = int(recv_args[2])

        # the client returns a message confirming it is ready to download the file
        clientSocket.send("OK\tRECEIVING\tReady to receive".encode())

        # the tqdm bar object helps keep track of the file size
        bar = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024, leave=False, colour="green")
        
        # opens the file and keeps writing to it while there are bytes still being received
        in_file = open(f"./downloads/{down_filename}", "wb")
        while True:

            # breaks the loop and closes the file once the number of transmitted bytes is equal to (or exceeds) the file size
            received_bytes = bar.n
            if received_bytes >= filesize:
                in_file.close()
                break

            message = clientSocket.recv(4096) # gets 4 kilobits at a time
            # the bytes received are used to update the bar object, the hash and the downloading file
            in_hash.update(message)
            in_file.write(message)
            bar.update(len(message))
        
        # the client then retransmits it hash of the file for comparison with the server
        clientSocket.send(in_hash.hexdigest().encode())
        time.sleep(1)
        del bar

        recv_msg = clientSocket.recv(1024).decode()
        recv_args = recv_msg.split("\t")

        # if the interaction has been successful, the server should send a message headed with SUCCESS
        if recv_args[0] == "SUCCESS":
            # client then double checks to see if the file has actually been receive
            # and sends an appropriate message to these server
            if(os.path.exists(f"./downloads/{down_filename}")):
                in_file_size = os.path.getsize(f"./downloads/{down_filename}")
                send_msg = "OK\tRECEIVED\t" + str(in_file_size)
                clientSocket.send(send_msg.encode())
            else:
                send_msg = "NOTOK\tNOTRECEIVED\tFile was not received"
                clientSocket.send(send_msg.encode())
            
            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            print(f"{filename} has been fully downloaded.")
        else:
            print("File invalid.")
    else:
        # prints out an error message if the server is not able to start transmitting the file
        print(recv_args[2])


def interactive_upload(clientSocket):
    # gives an opportunity for the user to enter name of a file and upload it to the server if there are no conflicting files

    # prompts the user for the path to file they want to upload and checks if it exists
    # the file path can either be relative or absolute
    fileExists = False
    while not fileExists:
        clear_ui(0.5)
        print_title("interactive upload")
        file_path = input("Specify the path of the file to upload:\n")
        fileExists = os.path.isfile(file_path)
        if not fileExists:
            print(f"File with path '{file_path}' does not exist")
            print("Try again")
        else:
            print(f"File '{file_path}' found")

    # the user is then prompted for the name they would like to save it as on the server and its password
    isValidName = False
    while not isValidName:
        clear_ui(0.5)
        print_title("interactive upload")
        print(f"Uploading {file_path}")
        out_filename = input("Enter a (valid) name you want to save it as on the server:\n")
        isValidName = check_name_validity(out_filename)

    file_password = input("Enter the password for the file (nothing if it's to be open): ")

    # uploads the file to the server
    upload(clientSocket, file_path, out_filename, file_password)

def upload(clientSocket, file_path, out_filename, file_password):
    # modular code to download a file from the server an save it in the downloads folder of the client'

    # sends a message, containing all the file detail, to the server to initiate interaction
    file_size = str(os.path.getsize(file_path))
    send_msg = "OK\tUPLOAD\t" + out_filename + "\t" + file_password + "\t" + file_size
    clientSocket.send(send_msg.encode())

    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    # if the server cannot receive the file then it sends an appropriate message
    # e.g. if the given filename already exists
    if recv_args[0] == "NOTOK":
        print(f"[SERVER]: {recv_args[1]}")
        return
    else:
        print(f"[SERVER]: {recv_args[1]}")


    out_hash = hashlib.md5() # hash object which will be used to compare to the uploaded file

    # sends the entire file in one packet to the server
    with open(file_path, "rb") as f:
        while True:
            data = f.read()
            if not data:
                break
            
            out_hash.update(data)
            clientSocket.sendall(data)

    # receives a message from the server containing the file's size on the server
    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    out_filesize = str(recv_args[1])
    if (file_size == out_filesize): 
        pass
        # print("Files are equal size")
    else:
        pass
        # print("Files are not equal size")

    # sends the hash for comparison and receives OK or NOTOK depending on whether the hashes match
    clientSocket.send(out_hash.hexdigest().encode())
    message = clientSocket.recv(1024).decode().split("\t")
    cmd = message[0]
    msg = message[1]
    if(cmd=="OK"):
        print(f"{out_filename} was uploaded")
    else:
        print(f"{msg}")
    

def batch_upload(clientSocket, folder_path, batch_password, recursive=False, keep_structure=False):
    """
    Function to upload an entire folder to the path under one password to save time

    params:
        *clientSocket*:     the socket on which to send the files
        *folder_path*:      the path to the folder containing all the files to be uploaded
                            (must be checked to ensure validity)
        *batch_password*:   the password to save all the files under
        *recursive*:        boolean flag; True denotes uploading all the contents in the folder
                            including those in subdirectories
        *keep_structure*:   still to be implemented (boolean flag that allows users to keep
                            folder structure when uploading recursively)
    """
    # gets a list of all the items in the folder
    dir_items = os.listdir(folder_path)

    for item in dir_items:
        file_path = folder_path + "/" + item
        if os.path.isfile(file_path):
            # if the item is a file it attempts to upload it to the server using its name and the batch password
            upload(clientSocket, file_path, item, batch_password)
        elif os.path.isdir(file_path):
            # if the item is a folder, it recursively calls the function to upload the items in that subfolder
            if recursive:
                batch_upload(clientSocket, file_path, batch_password, recursive=True)
        else:
            pass
    
def handshake(clientSocket):
    # extra handshake protocol to increase connection security
    send_msg = "HANDSHAKE\tTesting connection."
    clientSocket.send(send_msg.encode())

    recv_msg = clientSocket.recv(1024).decode()
    recv_args = recv_msg.split("\t")
    if recv_args[0] == "HANDSHAKE":
        return True, recv_args[1]
    else:
        return False, recv_args[1]
    

def get_server_files(clientSocket):
    """
    gets all the files in the serverfiles directory in an (ascending order)
    alphabetically ordered list

    returns:    the list and True if the request was successful, otherwise
                returns an empty list and False if the request was
                unsuccessful
    """

    # sends a request to the server asking to view all files 
    send_msg = "OK\tVIEW\tall"
    clientSocket.send(send_msg.encode())
    
    # receives either an OK with file names
    # or a not okay with an error message
    recv_msg = clientSocket.recv(4096).decode()
    recv_args = recv_msg.split("\t")
    if recv_args[0] == "SUCCESS":
        # print(recv_args[1])
        if recv_args[1] == 'The server directory is empty':
            return [], True

        files = (recv_args[1][:-1].split("\n"))
        files.sort()
        return files, True
    else:
        pass
    
    return [], True

def main():
    """
    The driver method for this entire client side application
    """
    clear_ui()
    # here the user logs in to a specific server over a specific port
    serverName, serverPort = request_serv_addr()

    clear_ui()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))

    # connection is established by this point
    addr = socket.gethostbyname(socket.gethostname())


    ## HANDSHAKE PROTOCOLS
    # sends a handshake protocol to establish message sending
    print(f"[You]: Initiating handshake protocol with server on {serverName}:{serverPort}", end="") 
    dots(5)

    status, msg = handshake(clientSocket)
    if not status:
        print(f"[SERVER]: {msg}")
        clientSocket.close()
    
    print(f"[SERVER]: {msg}", end="")
    dots(5)
    print("Handshaking complete.")
    clear_ui(2)
    ## HANDSHAKE ENDS


    # a user might want to log out while keeping the app open for other users
    appOpen = True
    while appOpen:

        ## LOG IN PROTOCOL
        loggedIn = False
        for i in range(1,4):
            # gives the user 3 attempts
            clear_ui(1)
            print_title("user login")
            print(f"attempt {i}/3\n")

            username = input("Username: ")
            password = getpass.getpass(prompt="Password: ")
            # sends the server the log in attempt info and the log
            log = f"\tLogin attempt {i} by {addr}: u: {username} p: {password}"
            send_msg = "LOGIN\t" + username + "\t" + password + log
            clientSocket.send(send_msg.encode())

            recv_msg = clientSocket.recv(1024).decode()
            recv_args = recv_msg.split("\t")

            print()
            # the client receives an appropriate message to its interaction with the server
            # breaks the loop if the user has been logged in
            if recv_args[0] == "ERROR":
                print(f"ERROR: {recv_msg[1].capitalize()}")
            elif recv_args[0] == "NOTAUTH":
                print(f"Authenication Error: {recv_args[1].capitalize()}")
            elif recv_args[0] == "AUTH":
                isAdmin = (recv_args[2] == "ADMIN")
                print(f"User: {username} successfully logged in as {recv_args[2]} user.")
                loggedIn = True
                break
        ##LOG IN ENDS

        ## MAIN FUNCTIONALITY
        while loggedIn:
            # present the menu to client
            clear_ui(1)
            print_title("main menu")
            print_menu(isAdmin)
            user_input = input("Enter the number of the option: \n")
            filename = "" # variable been initialised for later use in upload and download
            files_per_page = 10

            ## VIEW FILES FUNCTION
            if user_input == "1": #view files
                clear_ui(0.5)
                # sends a message to the server that it want's to view all files
                print_title("server files")

                # gets the files from the server and loads them into a list called files
                files, status = get_server_files(clientSocket)

                # if there is not items in the files list
                if len(files) == 0:
                    if status:
                        print("Server directory is empty")
                    else:
                        print("Error encountered on server side")

                    input("Press <ENTER> to return to view menu")
                    print("Returning to main menu", end="")
                    dots(3)
                    continue
                
                # prints out the pagination starting from page 1
                current_page = 1
                max_pages = math.ceil(len(files)/files_per_page)
                option = "d"
                while option:
                    clear_ui()
                    print_title("server files")
                    print_files(files, current_page, files_per_page=files_per_page)
                    print("\nEnter the number of the page to go to page, eg, '2' to go to page 2.")
                    print("Enter 'n' or 'p' to go the the next and previous pages respectively.")
                    print("Enter 'd' followed by then file index to download a file, eg, 'd3'.")
                    print("Enter nothing to return to main menu")
                    option = input("")

                    # does exactly what the instructions say and returns to the 
                    if option == "":
                        clear_ui()
                        print("Returning to main menu", end="")
                        dots(3)
                        continue
                    
                    # user enters the download option
                    elif option[0] == "d":
                        clear_ui(0.5)
                        print_title("interactive download")

                        # checks if the file index provided is valid otherwise continues to next iteration
                        try:
                            index = int(option[1:])
                            index = int(index)-1
                        except:
                            print("Error: invalid index")
                            time.sleep(1)
                            continue
                        if index > len(files) - 1:
                            print("Error: invalid index.")
                            time.sleep(1)
                            continue
                        
                        # makes an interactive download
                        filename = files[index].split("|")[0]
                        print(f"File chosen: {filename}")
                        down_filename = input("Enter the name you'd like to save the file under:\n")
                        isValidName = check_name_validity(down_filename)
                        while not isValidName:
                            down_filename = input("Enter the name you'd like to save the file under:\n")
                            isValidName = check_name_validity(down_filename)

                        download(clientSocket, filename, down_filename)
                        time.sleep(1)
                    
                    # next and previous page
                    elif option[0] == "p":
                        current_page = max(1, current_page-1)
                    elif option[0] == "n":
                        current_page = min(max_pages, current_page+1)
                    # user enters the page option
                    else:
                        clear_ui()
                        # checks if the page number is valid
                        try:
                            to_go_page = int(option)
                            if to_go_page > max_pages:
                                print("Error: invalid page number")
                                time.sleep(1)
                                continue
                            
                            current_page = to_go_page
                            # print_files(files, current_page, files_per_page=files_per_page)
                        except:
                            print("Error: invalid page number")
                            time.sleep(1)
                            continue             
                    # else:
                    #     print("Error: invalid input.")
            ## VIEW ENDS

            ## DOWNLOAD FUNCTION 
            elif user_input == "2":
                download_menu = True
                while download_menu:
                    # displays the menu to the user an option to download or return to the main menu
                    clear_ui(0.5)
                    print_title("download menu")
                    print("Select an option:\n\t1. Interactive Download\n\t2. Return to main menu\n")
                    input_2 = input("Enter the number of the option:\n")
                    if input_2 == "1":
                        downloading = True
                        while downloading:
                            clear_ui(0.5)
                            print_title("download file(s)")
                            interactive_download(clientSocket)

                            # after the user is done downloading the client then asks the user if they would like to download
                            # another file
                            clear_ui(1.5)
                            print_title("download file(s)")
                            input_3 = input("Would you like to download another file? (y/n): ")
                            while True:
                                if input_3=="y": break
                                elif input_3=="n":
                                    # print("no")
                                    downloading = False
                                    break
                                else:
                                    clear_ui()
                                    print_title("download file(s)")
                                    print("Error: invalid input")
                                    input_3 = input("Would you like to download another file? (y/n):\n")
                            
                    elif input_2 == "2":
                        clear_ui()
                        print("Returning to main menu", end="")
                        dots(3)
                        download_menu = False
                    else:
                        print("Error: invalid input")
            ## DOWNLOAD ENDS

            ## UPLOAD FUNCTION
            elif user_input == "3":
                upload_menu = True
                while upload_menu:
                    # displays the menu to the user an option to upload interactively or batch, or return to the main menu
                    clear_ui(0.5)
                    print_title("upload file(s)")
                    print("Select an option:\n\t1. Interactive Upload\n\t2. Batch/Folder Upload\n\t3. Return to menu\n")
                    input_2 = input("Enter the number of the option:\n")
                    if input_2 == "1":
                        uploading = True
                        while uploading:
                            clear_ui(0.5)
                            interactive_upload(clientSocket)

                            # after the user uploads the file, it asks them if they would like to upload another
                            clear_ui()
                            print_title("file upload")
                            input_3 = input("Would you like to upload another file? (y/n):\n")
                            while True:
                                if input_3=="y": break
                                elif input_3=="n":
                                    uploading = False
                                    break
                                else:
                                    clear_ui()
                                    print_title("file upload")
                                    print("Error: invalid input")
                                    input_3 = input("Would you like to download another file? (y/n): ")
                    
                    elif input_2 == "2":
                        clear_ui(0.5)
                        print_title("batch upload")

                        # keeps checking if the entered directory is valid until it gets a valid one
                        folder_path = input("Enter the path of the folder you would like to upload:\n")
                        while not os.path.isdir(folder_path):
                            folder_path = input("Enter the path of the folder you would like to upload:\n")
                        
                        batch_password = input("Enter the password to put on all the files (enter nothing to keep them open):\n")

                        check = input("Do you want to download files in the subdirectories recurively? (y/n)\n")
                        recursive = False
                        if check == "y": recursive = True
                        rec_str = " *recursively*" if recursive else ""

                        # gives the user one final check for confirmation
                        check = input(f"Are you sure you want to upload all the files in '{folder_path}'{rec_str} to the server? (y/n)\n")
                        
                        if check == "y":
                            batch_upload(clientSocket, folder_path, batch_password, recursive=recursive)
                            print("Batch upload complete")
                        else:
                            print("Batch upload cancelled")
                        input("Press <ENTER> to return to upload menu")
                        pass

                    elif input_2 == "3":
                        clear_ui()
                        upload_menu = False
                        print("Returning to main menu", end="")
                        dots(3)
                    else:
                        clear_ui(0.5)
                        print("Error: invalid input")
            ## UPLOAD ENDS

            ## LOG OUT FUNCTION
            elif user_input == "4":
                clear_ui()
                print_title("log out")

                # confirms if the user is sure they would like to log out before actually kicking them
                input_2 = input("Are you sure you want to log out? (y/n): ")

                while True:
                    if input_2=="y":
                        # logs the user out of the server and asks them if they would like ot keep the app open or not
                        clear_ui()
                        print_title("log out")
                        logout(clientSocket, username)
                        loggedIn = False
                        clear_ui()
                        print_title("close app?")
                        input_3 = input("Would you like to close the app? (y/n): ")
                        while True:
                            if input_3=="y":
                                # prints out a goodbye message when the user closes the app
                                clear_ui()
                                print_title("goodbye")
                                goodbye_msg = "Thank you for using the file sharing app :)"
                                for char in goodbye_msg:
                                    time.sleep(0.05)
                                    print(char, end="", flush=True)
                                time.sleep(0.2)
                                return
                            elif input_3=="n":
                                # print("no")
                                clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                clientSocket.connect((serverName,serverPort))
                                stats, msg = handshake(clientSocket)
                                if not status: return

                                # if the user does not close the app, it returns to the log in meny
                                print("Returning to log in page", end="")
                                dots(3)
                                break
                            else:
                                clear_ui()
                                print_title("close app?")
                                print("Error: invalid input")
                                input_3 = input("Would you like to close the app? (y/n): ")

                    elif input_2=="n":
                        # if the user does not close the app it returns
                        print("Returning to main menu", end="")
                        dots(3)
                        break
                    else:
                        clear_ui()
                        print_title("log out")
                        print("Error: invalid input")
                        input_2 = input("Are you sure you want to log out? (y/n): ")
            ## LOG OUT ENDS

            ## ADD USER
            elif user_input == "5" and isAdmin:
                admin_menu = True

                while admin_menu:
                    # presents the options to add a user or return to the main menu
                    clear_ui(0.5)
                    print_title("admin menu")
                    print("Select an option\n\t1. Add new user(s)\n\t2. Return to main menu")
                    input_2 = input("Enter the number of the option:\n")
                    if input_2 == "1":
                        # continues adding new users until the user specifies otherwise
                        adding_user = True
                        while adding_user:
                            clear_ui(0.5)
                            print_title("adding user")
                            interactive_add_user(clientSocket)

                            input_3 = input("Would you like to add another user? (y/n):\n")
                            while True:
                                if input_3=="y": break
                                elif input_3=="n":
                                    adding_user = False
                                    break
                                else:
                                    clear_ui()
                                    print_title("adding user")
                                    print("Error: invalid input")
                                    input_3 = input("Would you like to add another user? (y/n): ")
                    elif input_2=="2":
                        clear_ui()
                        admin_menu = False
                        print("Returning to main menu", end="")
                        dots(3)
                    else:
                        print("Error: invalid input")
            # ADD USER ENDS
            else:
                print("Invalid input")
        ## MAIN FUNCTIONALITY ENDS          

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        print("Forcefully disconnect from the server.")
