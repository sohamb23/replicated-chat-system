import socket, select, sys, errno

DEFAULT_SERVER_ADDR = '10.250.180.4'

class Client:
    def __init__(self, addr):
        self.header_length = 10
        self.username = ''
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((addr, 50051))
        self.socket.setblocking(False)
    
    def CreateAccount(self, username):
        # create a new account
        # return True if successful, False if username already exists
        self.username = username
        username_header = f"{len(username):<{header_length}}".encode('utf-8')
        self.socket.send(username_header + username)

        pass
    
    def DeleteAccount(self):
        # delete the current account
        # return True if successful, False if account does not exist
        pass

    def ListAccounts(self, wildcard=''):
        # list all accounts that match the wildcard
        # return a list of usernames
        pass

    def Login(self, username):
        # login to an existing account
        # return True if successful, False if account does not exist
        pass

    def Logout(self):

    
    def SendMessage(self, recipient, message):
        # send a message to another user
        # return True if successful, False if recipient does not exist
        pass

    def ListenForMessages(self):
        # receive a message from another user
        # return the sender and message
        pass

    # Print the menu for the client.
    def printMenu(self):
        print('1. Create Account')
        print('2. List All Accounts')
        print('3. List Account by Wildcard')
        print('4. Delete Account')
        print('5. Login')
        print('6. Send Message')
        print('7. Exit / Logout')

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
            username = input("Enter username: ")
            rpc_server = str(rpc_call).encode('utf-8')
            username = username.encode('utf-8')
            username_header = f"{len(username):<{header_length}}".encode('utf-8')
            client_socket.send(rpc_server + username_header + username)
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

    
    

ip = '127.0.0.1'
port = 8080
header_length = 10
username = input("Choose your username: ")


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, port))
client_socket.setblocking(False)

username = username.encode('utf-8')
username_header = f"{len(username):<{header_length}}".encode('utf-8')
client_socket.send(username_header + username)

while True:
    message = input(f"{username} > ")

    if message:
        message = message.encode('utf-8')
        message_header = f"{len(message):<{header_length}}".encode('utf-8')
        client_socket.send(message_header + message)
    try:
        while True:
            username_header = client_socket.recv(header_length)
            if not len(username_header):
                print("Connection closed by the server")
                sys.exit()
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket.recv(username_length).decode('utf-8')

            message_header = client_socket.recv(header_length)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            print(f"{username} > {message}")
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error', str(e))
            sys.exit()
        continue

    except Exception as e:
        print('General error', str(e))
        sys.exit()

recv_msg = client_socket.recv(1024)
print(recv_msg.decode('utf-8'))

send_msg = input('Enter user name(begin w/ the character @): ')
client_socket.send(send_msg.encode('utf-8'))

while True:
    recv_msg = client_socket.recv(1024)
    send_msg = input('Enter message: ')