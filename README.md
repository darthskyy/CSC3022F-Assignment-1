# CSC3022F-Assignment-1
This application uses TCP sockets for file transfer over a shared network. It follows a Client-Server model allowing several hosts to interact with a server at once.


## Running a server
Running `server.py` will start a server for your network. The server requires an encryption key to process user logins. If a key does not exist, one will be generated when trying to start the server. This adds a default user to the server.
- Username: admin
- Password: admin
The user then decides what port the server will be listening on. This is where incoming connections will be received.

## Running a client
The `client.py` script is used to run a client for the server. A server IP address and port number must be specified for a connection to be made. Each user requires a valid username and password to interact with the server. If a user provides incorrect login details three times, the server closes the connection and they must restart.
Once verified, the user will be presented with a menu of available options on the server.

## Adding users
Admin users are able to add users to the server. While logged in as an admin, use option 5 to add another user to the server. The admin must then provide a username and password for the new user.

### Authors
Tapera Chikumbu, Racquel Nina Dennison & Simbarashe Mawere
