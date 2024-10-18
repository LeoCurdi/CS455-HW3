import os
import socket

# the main client program
def clientProgram():
    # set up the connection to the server
    serverIPaddress, port = "localhost", 9999
    # creates a client socket using IPv4 (AF_INET) and TCP protocol (SOCK_STREAM)
    clientSocket = socket.socket() # socket.AF_INET, socket.SOCK_STREAM
    
    # Connect the client socket to the server using the localhost address
    clientSocket.connect((serverIPaddress, port))
    handleServerInteraction(clientSocket)

    # clean up
    clientSocket.close()
    print(f"Connection with {serverIPaddress} closed.")


# handles all communication with the server once the connection is accepted
def handleServerInteraction(clientSocket):
    # continuously send and receive data with the server
    while True:
        # client goes first, so client must send something
        if not sendCommunication(clientSocket):
            break

        # now it's the client's turn to recieve something back
        if not receiveCommunication(clientSocket):
            break


# sends a communication to the server. can be data or message
def sendCommunication(clientSocket):
    # ask the client what they want to do
    action = input("\n(1) send message, (2) send file, (3) exit:")

    if action == "1":
        # get the message from the client, send it to the server
        message = input("Enter the msg: ")
        clientSocket.send(b'MESG') # send an identifier, so the server knows to expect a message
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
        clientSocket.send(b'FILE') # send an identifier, so the server knows to expect a file
        clientSocket.send(f"copy_{fileName}".encode()) # rename the file so we can see the difference
        clientSocket.send(str(fileSize).encode().ljust(32)) # add in buffer space to ensure were sending the correct amount of bits for the server to read in

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
        clientSocket.send(b'EXIT') # send an identifier, so the server knows the client exited
        return False
    return True


# recieves a communication from the client, can be message or data
def receiveCommunication(clientSocket):
    # get the identifier that tells us what type of transaction were receiving
    responseType = clientSocket.recv(4).decode()
    
    # receive the transaction accordingly
    if responseType == 'MESG':
        response = clientSocket.recv(1024).decode()
        print("Message from server: ", str(response))
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

            # write the data to the target file
            file = open(fileName, "wb") # open a file for writing 
            file.write(fileBytes)
            file.close()
            print(f"\"{fileName}\" received successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    elif responseType == 'EXIT':
        print("Server has disconnected.\nExiting the chat . . .")
        return False
    else:
        print("Invalid response type: ", responseType)
    return True


# the main entry point for a python program
if __name__ == "__main__":
    clientProgram()