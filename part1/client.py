import socket
import threading
import sys
from server import SERVER_METHODS, SingleMessage, STREAM_CODE
import types
import selectors

DEFAULT_SERVER_ADDR = "10.250.180.4"
PORT = 50051

# selector for managing all sockets used by client
sel = selectors.DefaultSelector()

class Client:
    def __init__(self, sock, server_addr=DEFAULT_SERVER_ADDR):
        self.username = ''
        self.server_addr = server_addr
        self.sock = sock
        self.stop_listening = False # boolean to tell listener thread when user logs out

    # this encodes a method call, sends it to the server, and finally decodes and returns the
    # the server's response. Takes in a method name and the args to be passed to the method
    def run_service(self, method, args):
        assert method in SERVER_METHODS
        # SERVER_METHODS is a list of services/methods exposed by the server
        # grabbing the index of a method from this list gives a unique integer code
        # for the method in question
        method_code = SERVER_METHODS.index(method)
        transmission = str((method_code, args)).encode("utf-8")
        self.sock.sendall(transmission)
        data = self.sock.recv(1024)
        return eval(data.decode("utf-8"))

    # Create an account with the given username.
    def CreateAccount(self, usr=''):
        return self.run_service("CreateAccount", (usr,))

    # Delete the account with the client username.
    def DeleteAccount(self):
        success = self.run_service("DeleteAccount", (self.username,))
        if success:
            self.username = ''
        return success

    # List accounts on the server that match the wildcard
    def ListAccounts(self, wildcard='.*'):
        return self.run_service("ListAccounts", (wildcard,))

    # Login to the server with the given username.
    def Login(self, usr):
        success = self.run_service("Login", (usr,))
        if success:
            self.username = usr
        return success

    # Logout of the server.
    def Logout(self):
        success = self.run_service("Logout", (self.username,))
        if success:
            self.username = ''
        return success

    # Send a message to the given recipient.
    def SendMessage(self, recipient, message):
        return self.run_service("SendMessage", (self.username, recipient, message))

    # Listen for messages from the server.
    def ListenForMessages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # connect and initiate stream
            s.connect((self.server_addr, PORT))
            # STREAM_CODE is a code for the ChatStream method call on the server
            transmission = str((STREAM_CODE, (self.username,))).encode("utf-8")
            s.sendall(transmission)
            # setup selector to listen for read events
            data = types.SimpleNamespace(addr=self.server_addr, inb=b"", outb=b"")
            events = selectors.EVENT_READ
            sel.register(s, events, data=data)

            # process events and print messages received
            while not self.stop_listening:
                events = sel.select(timeout=None)
                for key, mask in events:
                    # data is none when the event is a new connection
                    if key.data is None:
                        raise Exception("Shouldn't be accepting connections to socket reserved for listening \
                                        to messages")
                    data = s.recv(1024)
                    msg = eval(data.decode("utf-8"))
                    assert type(msg) == SingleMessage
                    print()
                    print("[" + msg.sender + "]: " + msg.message)
    
    # Print the menu for the client.
    def printMenu(self):
        print('1. Create Account')
        print('2. List All Accounts')
        print('3. List Account by Wildcard')
        print('4. Delete Account')
        print('5. Login')
        print('6. Send Message')
        print('7. Exit / Logout')
    

# Run the client.
def run(server_addr = DEFAULT_SERVER_ADDR):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_addr, PORT))
        client = Client(s, server_addr)
        client.printMenu()
        user_input = input("Enter option: ")
        if user_input in ['1', '2', '3', '4', '5', '6', '7']:
            rpc_call = int(user_input)
        else:
            rpc_call = 0
        
        while rpc_call != 7:
            # create account
            if rpc_call == 1:
                name = input("Enter username: ")
                if client.CreateAccount(name):
                    print("Account created successfully")
                else:
                    print("Account creation failed")
            
            # list accounts
            elif rpc_call == 2:
                for account in client.ListAccounts():
                    print(account)

            # list accounts by wildcard
            elif rpc_call == 3:
                wildcard = input("Enter wildcard: ")
                for account in client.ListAccounts(wildcard):
                    print(account)
            
            # delete account
            elif rpc_call == 4:
                if client.username == '':
                    print("You must be logged in to delete your account")
                else:
                    if client.DeleteAccount():
                        print("Account deleted successfully")
                    else:
                        print("Account deletion failed")

            # login
            elif rpc_call == 5:
                usr = input("Enter username: ")
                if client.Login(usr):
                    print("Login successful")
                    # start a thread to listen for messages
                    t = threading.Thread(target=client.ListenForMessages)
                    t.start()
                else:
                    print("Login failed. Username might not exist.")

            # send message
            elif rpc_call == 6:
                if client.username == '':
                    print("You must be logged in to send messages")
                else:
                    recipient = input("Enter recipient: ")
                    message = input("Enter message: ")
                    if client.SendMessage(recipient, message):
                        print("Message sent successfully")
                    else:
                        print("Message failed to send")
            
            client.printMenu()
            user_input = input("Enter option: ")
            if user_input in ['1', '2', '3', '4', '5', '6', '7']:
                rpc_call = int(user_input)
            else:
                rpc_call = 0

        # Logout if the user is logged in
        if client.username != '':     
            client.Logout()
        # stop listening for messages
        client.stop_listening = True
        print('Exiting...')
        sys.exit(0)


# run the client
if __name__ == '__main__':
    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) == 2:
        run(server_addr = sys.argv[1])
    else:
        print("Invalid number of arguments: there is a single optional argument for the server's IP address")