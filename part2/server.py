import grpc
import chat_pb2
import chat_pb2_grpc
import re
from concurrent import futures
from threading import Lock
import socket
from collections import defaultdict

# Server class that implements the ChatServicer interface defined by proto file.
# This class is responsible for handling the RPC calls from the client.
class ChatServicer(chat_pb2_grpc.ChatServicer):

    # initialize the server with empty users, chats, and online lists
    def __init__(self):
        self.users_lock = Lock() # lock for both self.users and self.online
        self.users = set()
        self.chat_locks = defaultdict(lambda: Lock()) # locks for each k, v pair in self.chats
        self.chats = defaultdict(lambda: [])
        self.online = set()

    # report failure if account already exists and add user otherwise
    def CreateAccount(self, request, context):
        user = request.accountName
        with self.users_lock:
            success = user not in self.users
            if success:
                print("adding user: " + user)
                self.users.add(user)
        return chat_pb2.CreateAccountResponse(success=success)
    
    # report failure if account doesn't exist and delete user otherwise
    def DeleteAccount(self, request, context):
        user = request.accountName
        with self.users_lock:
            success = user in self.users
            if success:
                print("deleting user: " + user)
                self.users.discard(user)
                self.online.discard(user)
                with self.chat_locks[user]:
                    del self.chats[user] # delete undelivered chats if you are deleting the account
                del self.chat_locks[user]
        return chat_pb2.DeleteAccountResponse(success=success)
    
    # report failure if account doesn't exist and return list of accounts that match wildcard otherwise
    def ListAccounts(self, request, context):
        # search in users for accounts that match wildcard
        pattern = re.compile(request.accountWildcard)
        with self.users_lock:
            accounts = list(filter(lambda user: pattern.search(user) != None, self.users))
        print("listing users: " + str(accounts))
        return chat_pb2.ListAccountsResponse(accounts=accounts)

    # report failure if account doesn't exist and add user to online list otherwise
    def Login(self, request, context):
        user = request.accountName
        print("logging in user: " + user)
        with self.users_lock:
            self.online.add(user)
            success = user in self.users
        return chat_pb2.LoginResponse(success=success)

    # report failure if account doesn't exist and remove user from online list otherwise
    def Logout(self, request, context):
        user = request.accountName
        print("logging out user: " + user)
        with self.users_lock:
            success = user in self.online
            self.online.discard(user)
        return chat_pb2.LogoutResponse(success=success)

    # report failure if recipient doesn't exist and send message otherwise
    def SendMessage(self, request, context):
        sender = request.sender
        recipient = request.recipient
        message = request.message
        print(f"received message from {sender} to {recipient}: {message}")
        self.users_lock.acquire(blocking=True)
        if recipient not in self.users:
            self.users_lock.release()
            return chat_pb2.MessageSendResponse(success=False)
        else:
            self.users_lock.release()
            message = chat_pb2.SingleMessage(sender=sender, message=message)
            with self.chat_locks[recipient]:
                self.chats[recipient].append(message)
            return chat_pb2.MessageSendResponse(success=True)

    # report failure if account doesn't exist and start chat stream otherwise
    def ChatStream(self, request, context):
        user = request.accountName
        print(f"started chat stream for {user}")
        # always make sure to release this; note that this needs to intermittently release
        self.users_lock.acquire(blocking=True)
        while user in self.online:
            assert user in self.users, "user does not exist or no longer exists"
            # release so that the streams aren't constantly holding onto the lock
            self.users_lock.release()
            with self.chat_locks[user]:
                if self.chats[user]:
                    print("sending message to " + user)
                    yield self.chats[user].pop(0)
            # reacquire lock before checking while condition
            self.users_lock.acquire(blocking=True)
        # release lock before stopping stream
        self.users_lock.release()

# start the server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server) 

    ip_address = socket.gethostbyname(socket.gethostname()) # get ip address of server
    server.add_insecure_port(ip_address + ':50051')         # add port to ip address

    print("starting server at " + ip_address)
    server.start()
    server.wait_for_termination()

# run the server when this script is executed
if __name__ == '__main__':
    serve()
    