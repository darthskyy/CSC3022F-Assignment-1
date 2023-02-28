from cryptography.fernet import Fernet
import os.path
from time import time
import os
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
def downloads(connection,address,textfileName):
    directory,textfile = textfileName.split(' ')
    print(f"Checking if the file with name {textfile} exists")
    if(os.path.exists(textfile)):
        print(f"File {textfile} exixts!")
        print(f"Downloading file {textfile} into directory {directory}")
        file = open(f"./serverfiles/{textfile}","r")
        data=file.read()
        connection.send(data.encode("utf-8"))
        file.close()
        print("File has been sent!")
    else:
        print(f"The file under the name {textfile} does not exist")

def viewFiles(connection):
        files = os.listdir("serverfiles")
        send_data = "OK@"
        if len(files) == 0:
            send_data += "The server directory is empty"
        else:
            send_data += "\n".join(f for f in files)
        connection.send(send_data.encode(FORMAT))

def upload (socket, name, size):
    
    bar = tqdm(range(size), f"Receiving {name}", unit="B", unit_scale=True, unit_divisor=1024)
    f = open(f"./serverfiles/recv_{name}", "wb")
    while True:
        message = socket.recv(4096)
        if not message:
            break
        f.write(message)
        
        bar.update(len(message))

    f.close    
    socket.close()


