import chat_pb2
import chat_pb2_grpc
import grpc
import threading
import sys

DEFAULT_SERVER_ADDR = '10.250.180.4'
# c's address: '10.228.32.66'

# Client class. The class we will use to interact with the server.
class Client:

    # initialize the client with the server's address and create a stub.
    def __init__(self, addr=DEFAULT_SERVER_ADDR):
        self.username = ''
        self.addr = addr
        self.channel = grpc.insecure_channel(addr + ":50051")
        self.stub = chat_pb2_grpc.ChatStub(self.channel)

    # Create an account with the given username.
    def CreateAccount(self, usr=''):
        response = self.stub.CreateAccount(chat_pb2.CreateAccountRequest(accountName= usr if usr != '' else self.username))
        return response.success

    # Delete the account with the client username.
    def DeleteAccount(self):
        response = self.stub.DeleteAccount(chat_pb2.DeleteAccountRequest(accountName=self.username))
        return response.success

    # List accounts on the server that match the wildcard
    def ListAccounts(self, wildcard='.*'):
        response = self.stub.ListAccounts(chat_pb2.ListAccountsRequest(accountWildcard = wildcard))
        return response.accounts

    # Login to the server with the given username.
    def Login(self, usr):
        response = self.stub.Login(chat_pb2.LoginRequest(accountName=usr))
        if response.success:
            self.username = usr
        return response.success

    # Logout of the server.
    def Logout(self):
        response = self.stub.Logout(chat_pb2.LogoutRequest(accountName=self.username))
        if response.success:
            self.username = ''
        return response.success

    # Send a message to the given recipient.
    def SendMessage(self, recipient, message):
        response = self.stub.SendMessage(chat_pb2.MessageSendRequest(sender=self.username, recipient=recipient, message=message))
        return response.success

    # Listen for messages from the server.
    def ListenForMessages(self):
        for msg in self.stub.ChatStream(chat_pb2.ChatRequest(accountName=self.username)):
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
def run(addr = DEFAULT_SERVER_ADDR):
    client = Client(addr)
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
                client.Logout() # logout before deleting account    
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
    print('Exiting...')
    exit()

# run the client
if __name__ == '__main__':
    if len(sys.argv) == 1:
        run()
    elif len(sys.argv) == 2:
        run(addr = sys.argv[1])
    else:
        print("Invalid number of arguments: there is a single optional argument for the server's IP address")