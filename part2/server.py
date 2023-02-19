import grpc
import chat_pb2
import chat_pb2_grpc
import re
import ping3
from concurrent import futures

# Server class that implements the ChatServicer interface defined by proto file.
# This class is responsible for handling the RPC calls from the client.
class ChatServicer(chat_pb2_grpc.ChatServicer):

    # initialize the server with empty users, chats, and online lists
    def __init__(self):
        self.users = set()
        self.chats = dict()
        self.online = set()

    # report failure if account already exists and add user otherwise
    def CreateAccount(self, request, context):
        success = request.accountName not in self.users
        if success:
            print("adding user: " + request.accountName)
            self.users.add(request.accountName)
            self.chats[request.accountName] = []
        return chat_pb2.CreateAccountResponse(success=success)
    
    # report failure if account doesn't exist and delete user otherwise
    def DeleteAccount(self, request, context):
        success = request.accountName in self.users
        if success:
            print("deleting user: " + request.accountName)
            self.users.discard(request.accountName)
            self.online.discard(request.accountName) if request.accountName in self.online else print("user is not online")
            del self.chats[request.accountName] # delete undelivered chats if you are deleting the account
        return chat_pb2.DeleteAccountResponse(success=success)
    
    # report failure if account doesn't exist and return list of accounts that match wildcard otherwise
    def ListAccounts(self, request, context):
        # search in users for accounts that match wildcard
        pattern = re.compile(request.accountWildcard)
        accounts = list(filter(lambda user: pattern.search(user) != None, self.users))
        print("listing users: " + str(accounts))
        return chat_pb2.ListAccountsResponse(accounts=accounts)

    # report failure if account doesn't exist and add user to online list otherwise
    def Login(self, request, context):
        print("logging in user: " + request.accountName)
        self.online.add(request.accountName)
        return chat_pb2.LoginResponse(success=request.accountName in self.users)

    # report failure if account doesn't exist and remove user from online list otherwise
    def Logout(self, request, context):
        print("logging out user: " + request.accountName)
        self.online.remove(request.accountName)
        return chat_pb2.LogoutResponse(success=request.accountName not in self.online)

    
    # report failure if recipient doesn't exist and send message otherwise
    def SendMessage(self, request, context):
        print(f"received message from {request.sender} to {request.recipient}: {request.message}")
        if request.recipient not in self.users:
            return chat_pb2.MessageSendResponse(success=False)
        else:
            # TODO: add locking for self.chats
            message = chat_pb2.SingleMessage(sender=request.sender, message=request.message)
            self.chats[request.recipient].append(message)
            return chat_pb2.MessageSendResponse(success=True)

    # report failure if account doesn't exist and start chat stream otherwise
    def ChatStream(self, request, context):
        user = request.accountName
        print(f"started chat stream for {user}")
        while user in self.online:
            assert user in self.users, "user does not exist or no longer exists"
            # TODO: add locking for self.chats
            if self.chats[user]:
                print("sending message to " + user)
                yield self.chats[user].pop(0)

# start the server
def serve(ip_address):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port(ip_address + ':50051')
    print("starting server")
    server.start()
    server.wait_for_termination()

# run the server when this script is executed
if __name__ == '__main__':
    ip_address = input("Enter your ip address: ")
    serve(ip_address)
    