import chat_pb2
import chat_pb2_grpc
import grpc
import threading
import sys
import time

SERVER_ADDRS = {1: "10.250.11.129:50051", 2: "10.250.11.129:50052", 3: "10.250.11.129:50053", 4: "10.250.147.180:50051", 5: "10.250.147.180:50052", 6: "10.250.147.180:50053"}


# Client class. The class we will use to interact with the server.
class Client:

    # initialize the client with the server's address and create a stub.
    def __init__(self, addr=SERVER_ADDRS[1]):
        self.username = ''
        self.addr = addr
        self.channel = grpc.insecure_channel(addr)
        self.primary_id = 1
        self.stub = chat_pb2_grpc.ChatStub(self.channel)
        self.stop_listening = False # boolean to tell listener thread when user logs out
        self.stream = None # stream to listen for messages on

        # start a thread to connect to the primary server and update this connection
        self.connection_thread = threading.Thread(target=self.connectPrimary)
        self.connection_thread.start()

    def connectPrimary(self): 
        while True:
            try:
                response = self.stub.GetPrimaryServerId(chat_pb2.Empty())
                if response.serverId != self.primary_id:
                    self.primary_id = response.serverId
                    self.channel = grpc.insecure_channel(SERVER_ADDRS[self.primary_id])
                    self.stub = chat_pb2_grpc.ChatStub(self.channel)
            except Exception as e:
                self.primary_id += 1
                if self.primary_id > 6:
                    print("all servers down. try again later.")
                    sys.exit()
                self.channel = grpc.insecure_channel(SERVER_ADDRS[self.primary_id])
                self.stub = chat_pb2_grpc.ChatStub(self.channel)
            time.sleep(0.2)
    #Create an account with the given username.
    def CreateAccount(self, usr=''):
        response = self.stub.CreateAccount(chat_pb2.CreateAccountRequest(accountName=usr, fromPrimary = False))
        return response.success

    # Delete the account with the client username.
    def DeleteAccount(self):
        response = self.stub.DeleteAccount(chat_pb2.DeleteAccountRequest(accountName=self.username, fromPrimary = False))
        if response.success:
            self.username = ''
        return response.success

    # List accounts on the server that match the wildcard
    def ListAccounts(self, wildcard='.*'):
        response = self.stub.ListAccounts(chat_pb2.ListAccountsRequest(accountWildcard = wildcard))
        return response.accounts

    # Login to the server with the given username.
    def Login(self, usr):
        response = self.stub.Login(chat_pb2.LoginRequest(accountName=usr, fromPrimary = False))
        if response.success:
            self.username = usr
        return response.success

    # Logout of the server.
    def Logout(self):
        response = self.stub.Logout(chat_pb2.LogoutRequest(accountName=self.username, fromPrimary = False))
        if response.success:
            self.username = ''
        return response.success

    # Send a message to the given recipient.
    def SendMessage(self, recipient, message):
        request = chat_pb2.MessageSendRequest(sender=self.username, recipient=recipient, message=message, fromPrimary = False)
        response = self.stub.SendMessage(request)
        return response.success

    # Listen for messages from the server.
    def ListenForMessages(self):
        self.stream = self.stub.ChatStream(chat_pb2.ChatRequest(accountName=self.username, fromPrimary = False))
        while not self.stop_listening:
            try: 
                msg = next(self.stream)
                print()
                print("[" + msg.sender + "]: " + msg.message)
            except Exception as e:
                print(str(e))
                self.stream = self.stub.ChatStream(chat_pb2.ChatRequest(accountName=self.username, fromPrimary = False))
            time.sleep(0.5)
    # List all messages sent to the client.
    def PrintMessages(self):
        try:
            response = self.stub.PrintMessages(chat_pb2.PrintMessagesRequest(accountName=self.username))
            return response.messages
        except Exception as e:
            print("Error: " + str(e))

    # Print the menu for the client.
    def printMenu(self):
        print('1. Create Account')
        print('2. List All Accounts')
        print('3. List Account by Wildcard')
        print('4. Delete Account')
        print('5. Login')
        print('6. Send Message')
        print('7. List all messages')
        print('8. Exit / Logout')
    

# Run the client.
def run(addr = SERVER_ADDRS[1]):
    client = Client(addr)
    client.printMenu()
    user_input = input("Enter option: ")
    if user_input in ['1', '2', '3', '4', '5', '6', '7']:
        rpc_call = int(user_input)
    else:
        rpc_call = 0
    
    while rpc_call != 8:
        # create account
        if rpc_call == 1:
            name = input("Enter username: ")
            if client.CreateAccount(name):
                print("Account created successfully")
            else:
                print("Account creation failed")
        
        # list accounts
        elif rpc_call == 2:
            print(client.ListAccounts(''))

        # list accounts by wildcard
        elif rpc_call == 3:
            wildcard = input("Enter wildcard: ")
            print(client.ListAccounts(wildcard))
        
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
                print("Login failed. Username might not exist or you might not be connected to the primary server.")


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
        
        # list messages
        elif rpc_call == 7:
            if client.username == '':
                print("You must be logged in to list messages")
            else:
                msgs = client.PrintMessages()
                if msgs:
                    for msg in msgs:
                        print("[" + msg.sender + "]: " + msg.message)
        
        client.printMenu()
        user_input = input("Enter option: ")
        if user_input in ['1', '2', '3', '4', '5', '6', '7', '8']:
            rpc_call = int(user_input)
        else:
            rpc_call = 0

    # Logout if the user is logged in
    if client.username != '':
        client.Logout()
    client.stop_listening = True
    print('Exiting...')
    sys.exit(0)

# run the client
if __name__ == '__main__':
    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) == 2:
        run(addr = sys.argv[1])
    else:
        print("Invalid number of arguments: there is a single optional argument for the server's IP address")