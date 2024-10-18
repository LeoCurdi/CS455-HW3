import socket
import tqdm # for progress bars
import threading # for multiple client connections
import os

# the main server program
def serverProgram():
    # set up the server socket
    serverIPaddress, port = "localhost", 9999
    # creates a server socket using IPv4 (AF_INET) and TCP protocol (SOCK_STREAM)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind server to localhost so it can accept all connections
    serverSocket.bind((serverIPaddress, port))
   
    # set the server to listen mode, with the max amount of backlogged connections
    serverSocket.listen(5)
    print(f"Server {serverIPaddress} is listening on port {port}...")

    # accept connection, create a new socket for the client and the cleint's address
    clientSocket, clientAddress = serverSocket.accept()
    print(f"Client {clientAddress} connected.")
    handleClientInteraction(clientSocket)

    # close the connection with the client to free up resources
    clientSocket.close()
    print(f"Connection with {clientAddress} closed.")


# handles all communication with one individual client once they are connected
def handleClientInteraction(clientSocket):
    # continuously send and receive data with the client
    while True:
        # client goes first, so server must receive first
        if not receiveCommunication(clientSocket):
            break

        # now it's the server's turn to send something back
        if not sendCommunication(clientSocket):
            break


# recieves a communication from the client, can be message or data
def receiveCommunication(clientSocket):
    # get the identifier that tells us what type of transaction were receiving
    responseType = clientSocket.recv(4).decode()
    
    # receive the transaction accordingly
    if responseType == 'MESG':
        response = clientSocket.recv(1024).decode()
        print("Message from client: ", str(response))
    elif responseType == 'FILE':
        try:
            # get the file name and size
            fileName = clientSocket.recv(1024).decode()
            fileSize = int(clientSocket.recv(32).decode().strip()) # strip the buffer space and convert to an integer
            print(f"Received a file from {clientSocket}.\nFile name: \"{fileName}\".\nFile size: {fileSize}\nLoading file . . .")

            # create an empty string to copy the data to
            fileBytes = b""
            # read in the file data from the client and copy it to the target until we hit the end tag
            while True:
                data = clientSocket.recv(1024)
                fileBytes += data
                if fileBytes[-11:] == b"<endOfFile>":
                    fileBytes = fileBytes[:-11]  # Remove the end tag
                    break

            # write the data to a target file
            file = open(fileName, "wb") # open a file for writing 
            file.write(fileBytes)
            file.close()
            print(f"\"{fileName}\" received successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    elif responseType == 'EXIT':
        print("Client has disconnected.\nExiting the chat . . .")
        return False
    else:
        print("Invalid response type: ", responseType)
    return True


# sends a communication to the client. can be data or message
def sendCommunication(clientSocket):
    # ask the server what they want to do
    action = input("\n(1) send message, (2) send file, (3) exit:")

    if action == "1":
        # get the message from the server, send it to the client
        message = input("Enter the msg: ")
        clientSocket.send(b'MESG') # send an identifier, so the client knows to expect a message
        clientSocket.send(bytes(message, 'ascii'))
    elif action == "2":
        # ask the user for a file
        fileName = input("Enter the name of a file to transfer: ")
        
        # check if the file is valid
        if not os.path.isfile(fileName):
            print("File does not exist. Please try again.")
            return True
        
        # send the metadata (file name and its size)
        fileSize = os.path.getsize(fileName) # so we can tell the server how big the file is
        clientSocket.send(b'FILE') # send an identifier, so the client knows to expect a file
        clientSocket.send(f"copy_{fileName}".encode()) # rename the file so we can see the difference
        clientSocket.send(str(fileSize).encode().ljust(32)) # add in buffer space to ensure were sending the correct amount of bits for the client to read in

        # send the file data itself
        file = open(fileName, "rb") # open the file in read byte mode
        data = file.read()
        file.close()
        clientSocket.sendall(data)

        # send an ending tag to mark the end of the file transmission
        clientSocket.send(b"<endOfFile>")
        print(f"\"{fileName}\" sent successfully.")
    else:
        print("Exiting the chat . . .")
        clientSocket.send(b'EXIT') # send an identifier, so the client knows the server exited
        return False
    return True


# the main entry point for a python program
if __name__ == "__main__":
    serverProgram()