from cryptography.fernet import Fernet
import os.path
from time import time
import os
import hashlib
import sys
from tqdm import tqdm


FORMAT = "utf-8"

# User authentication methods
def get_key():
    """
    Gets the encryption key for the server
    """
    # maybe make a function that updates the key after some time
    # this function then has to rewrite the users.bin file
    try:
        with open("./filekey.key", "rb") as filekey:
            key = filekey.read()
    except:
        # return false if there was a complication in open the file
        return False

    fernet = Fernet(key)
    return fernet

def login(username, passwd):
    """
    Method to login users into the server.

    params:
        username: the user's unique username in the server
        passwd: the user's secret password
    
    return:
        True if the username and password combination exists in the server otherwise False.
    """

    # reading in the encryption key
    if not os.path.isfile("./users.bin"):
        return [False, "NOTAUTH\tuser database could not be found"]
    
    fernet = get_key()
    if fernet==False:
        return [False, "NOTAUTH\tserver file encryption error."]

    # reading in the users into a list
    try:
        with open("./users.bin", "rb") as users:
            all_users = users.read()
    except Exception as e:
        print(e)
        return [False, "NOTAUTH\tserver user file encryption error."]
    
    all_users_str = fernet.decrypt(all_users).decode()
    all_users_list = all_users_str.split("\r\n")
    all_users_list.pop()


    for user in all_users_list:
        u, p = user.split(",")
        if (u==username):
            if (p==passwd):
                return [True, "AUTH\tUser has been logged in successfully"]
            else:
                return [False, "NOTAUTH\twrong password"]
    
    return [False, "NOTAUTH\tuser is not registered on the server"]


def add_user(username, passwd):
    """
    Adds a user into the server system

    params:
        username: a string of the username (should be unique), should not contain a comma ',' character
        passwd: the user's password, again must not contain a comma ',' character
    
    return:
        True, and confirmation message, if the user was added successfully otherwise False
    """

    # the thing that will be entered into the file
    hashed = username + "," + passwd
    
    # gets the hash key from the file
    fernet = get_key()
    if fernet==False:
        return False, "Error: server encryption error."

    isNew = False
    # reads the users file and decrypts it then checks if the user is there
    if not os.path.isfile("./users.bin"):
        isNew = True
        x = open("./users.bin", "x")
        x.close()

    if not isNew:
        with open(f"./users.bin", "rb") as f:
            all_users = f.read()

        all_users_str = fernet.decrypt(all_users).decode()
        all_users_list = all_users_str.split("\r\n")


        for user in all_users_list:
            if username in user:
                return False, f"Error: user {username} is already registered"

        all_users_str += hashed + "\r\n"
        all_users = fernet.encrypt(all_users_str.encode())

        with open(f"./users.bin", "wb") as f:
            f.write(all_users)
            return True, f"User {username} has been added"
    else:
        hashed += "\r\n"
        x = fernet.encrypt(hashed.encode())
        with open(f"./users.bin", "wb") as f:
            f.write(x)
            return True, f"User {username} has been added"
   

def user_exists(username: str):
    """
    Method to check if a user exists in the server.

    params:
        username: the user's unique username in the server
    
    return:
        True if the user exists in the server otherwise False.
    """
    start = time()
    # reading in the encryption key
    if not os.path.isfile("./users.bin"):
        return False, "Error: user database could not be found"
    
    fernet = get_key()
    if fernet==False:
        return False, "Error: server encryption error."

    # reading in the users into a list
    with open("./users.bin", "rb") as users:
        all_users = users.read()
    
    all_users_str = fernet.decrypt(all_users).decode()
    all_users_list = all_users_str.split("\r\n")
    all_users_list.pop()


    for user in all_users_list:
        u, p = user.split(",")
        if (u==username):
            end = time()
            print(f"Time taken: {end-start} seconds")
            return True
    
    end = time()
    print(f"Time taken: {end-start} seconds")
    return False

def delete_user(username: str):
    """
    Deletes a user from the server files

    params:
        username: the name of the user who is to be deleted from the server
    
    return:
        True if the user has been successfully deleted otherwise False

    """
    if not user_exists(username): return False, "Error: user does not exist"
    
    # gets the hash key from the file
    fernet = get_key()
    if fernet==False:
        return False, "Error: server encryption error."

    with open("./users.bin", "rb") as users:
        all_users = users.read()
    
    all_users_str = fernet.decrypt(all_users).decode()
    all_users_list = all_users_str.split("\r\n")

    
    for i in range(len(all_users_list)):
        u, p = all_users_list[i].split(",")
        if u==username:
            del all_users_list[i]
            break
    
    all_users_str = "\r\n".join(all_users_list)
    write_data = fernet.encrypt(all_users_str.encode())
    
    with open("./users.bin", "wb") as users:
        all_users = users.write(write_data)
        # print(username, "was deleted from the user list")

    return True, "User has been successfully removed from the server"

# file transfer methods
def download(connection, textfile):
    print(f"Checking if the file with name {textfile} exists")
    if(os.path.exists(f"./serverfiles/{textfile}")):
        print(f"File {textfile} exixts!")
        print(f"Downloading file {textfile} into directory ") #directory decided by client
        out_file = open(f"./serverfiles/{textfile}","rb") #changed to rb so no need to encode
        out_hash = hashlib.md5() #hash buffer of given size
        # sends the file size so that the client can prepare the space
        out_file_size = os.path.getsize(f"./serverfiles/{textfile}")
        send_msg = "TRANSMITTING\t" + str(out_file_size)
        connection.send(send_msg.encode()) #send filesize so client knows how many bytes to expect
        
        status = connection.recv(1024).decode()
        if status == "OK":
            bar = tqdm(range(out_file_size), f"Sending {textfile}", unit ="B", unit_scale=True, unit_divisor = 1024)
            while True:
                data = out_file.read(4096)
                if not data:
                    break
                out_hash.update(data) #add data to hash buffer
                connection.sendall(data)
                bar.update(len(data))

            out_file.close()
        print(f"\n\nhash is : {out_hash.hexdigest()}")
        in_hash = connection.recv(1024).decode()
        hashed : bool = (in_hash == out_hash.hexdigest())
        
        return out_file_size, hashed
    else:
        send_msg = f"NOTTRANSMITTING\tFile: {textfile} could not be found"
        connection.send(send_msg.encode())
        print(f"The file under the name {textfile} does not exist")
        return -1, False

def viewFiles(server_data_files):
    """
    Method to view the files in a server. Under the server directory.
    params:
        connection: The connection with the server
        server_data_files: The directory where all the files are stored
    Connects to the client and sends the files in the directory. 
    """
    try:
        files = os.listdir(server_data_files)
        send_data_user = "OK\t" # this will be a decoding mechanism that the user will use
        if len(files) == 0:
            send_data_user += "The server directory is empty"
        else:
            send_data_user += "\n".join(f for f in files) # listing the files in the directory
        
        return [True, send_data_user]
    except Exception as e:
        print(e)
        return [False, "NOTOK\tUnexpected error encountered."]

    return


def upload (connection, filename, filesize):
    """
        Method to upload the files to the server, under the client directory directory.
        params:
            socket: The connection with the client
            name: The directory where all the files are stored and the name of the file. 
            size: size used for the tqdm bar update
        Connects to the client, retrieves the files that they want to upload and uploads the files to the
        specified directory 
    """
    # displaying on the cmd to show the progress of uploading the files
    bar = tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    upload_file = open(f"./serverfiles/{filename}", "wb")
    while True:
        received_bytes = bar.n
        if received_bytes >= filesize:
            break

        filedata = connection.recv(4096)
        upload_file.write(filedata)
        bar.update(len(filedata))

    upload_file.close() 
    if(os.path.exists(f"./serverfiles/{filename}")):
        connection.send("OK\tFile has been successfully uploaded.".encode())
        print("Successfully uploaded.")
    else:
        connection.send("NOTOK\tFile has not been successfully uploaded.".encode())
        print("File upload has failed.")
