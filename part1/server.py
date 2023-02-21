import socket, select
import re
from collections import defaultdict
from threading import Lock

DEFAULT_SERVER_ADDR = '127.0.0.1'
DEFAULT_PORT = 8080
header_length = 10

# socket_list = []
# users = {} #connected users - socket is the key and the username and data is the value

# server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
# server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse address set to 1 on socket to avoid error
# server_socket.bind((ip, port)) #bind socket to ip and port

# server_socket.listen() #listen for connections
# socket_list.append(server_socket) #add socket to socket_list


class Server:
    def __init__(self, addr = DEFAULT_SERVER_ADDR, port = DEFAULT_PORT):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse address set to 1 on socket to avoid error
        self.server_socket.bind((addr, port)) #bind socket to ip and port

        self.server_socket.listen()
        self.socket_list = [self.server_socket]

        self.users_lock = Lock() # lock for both self.users and self.online
        self.users = set()
        self.chat_locks = defaultdict(lambda: Lock()) # locks for each k, v pair in self.chats
        self.chats = defaultdict(lambda: [])
        self.online = set()
        self.header_length = 10

    def CreateAccount(self, username):
        # create a new account
        # return True if successful, False if username already exists
        # decode the username form utf-8
        with self.users_lock:
            if username in self.users:
                return False
            self.users.add(username)
            return True
    
    def DeleteAccount(self, username):
        # delete the current account
        # return True if successful, False if account does not exist
        with self.users_lock:
            success = user in self.users
            if success:
                print("deleting user: " + user)
                self.users.discard(user)
                self.online.discard(user)
                with self.chat_locks[user]:
                    del self.chats[user] # delete undelivered chats if you are deleting the account
                del self.chat_locks[user]
    
    def ListAccounts(self, wildcard=''):
        # list all accounts that match the wildcard
        # return a list of usernames
        pattern = re.compile(wildcard)
        with self.users_lock:
            accounts = list(filter(lambda user: pattern.search(user) != None, self.users))
        print("listing users: " + str(accounts))
        return str(accounts)
    
    def Login(self, username):
        # login to an existing account
        # return True if successful, False if account does not exist
        with self.users_lock:
            if username in self.users:
                self.online.add(username)
                return True
            return False
    
    def Logout(self, username):
        # logout of the current account
        # return True if successful, False if account is not logged in
        with self.users_lock:
            if username in self.online:
                self.online.discard(username)
                return True
            return False
    
    def SendMessage(self, sender, recipient, message):
        # send a message to another user
        # return True if successful, False if recipient does not exist
        with self.users_lock:
            if recipient in self.users:
                with self.chat_locks[recipient]:
                    self.chats[recipient].append((sender, message))
                return True
            return False
    
    


def receive_message(client_socket):
    # 
    try:
        message_header = client_socket.recv(header_length + 1)

        if not len(message_header):
            return False
        
        code = int(message_header[:1].decode('utf-8').strip())
        message_length = int(message_header[1:].decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False

def serve():
    server = Server()
    while True:
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], socket_list)

        for socketClient in read_sockets:
            if socketClient == server_socket:
                socketfd, socketaddr = server_socket.accept()
                user = receive_message(socketfd)

                if user is False:
                    continue

                socket_list.append(socketfd)
                users[socketfd] = user
                print('Connected by', socketaddr)
            else:
                message = receive_message(socketClient)
                    
                user = users[socketClient]
                print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

                for client in users:
                    if client != socketClient:
                        client.send(user['header'] + user['data'] + message['header'] + message['data'])
                
        for socketClient in error_sockets:
            socket_list.remove(socketClient)
            del users[socketClient]


if __name__ == '__main__':
    serve()





            # try:
            #     data = socketClient.recv(1024)
            #     if data.startswith("/quit"):
            #         sock.close()
            #         socket_list.remove(sock)
            #         del users[sock]
            #         continue
            #     if data.startswith("@"):
            #         users[data[1:].lower()] = sockfd
            #         sockfd.send("User added")
            #     else:
            #         for client_socket in socket_list:
            #             if client_socket != sock:
            #                 client_socket.send(data)
            # except ConnectionResetError:
            #     sock.close()
            #     socket_list.remove(sock)
            #     del users[sock]
            #     continue
server_socket.close()
