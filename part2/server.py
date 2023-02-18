import grpc
import chat_pb2
import chat_pb2_grpc
import futures
import re

class ChatServicer(chat_pb2_grpc.ChatServicer):

    def __init__(self):
        self.users = set()
        self.chats = dict()

    # report failure if account already exists and add user otherwise
    def CreateAccount(self, request, context):
        success = request.accountName not in self.users
        if success:
            self.users.add(request.accountName)
        return chat_pb2.CreateAccountResponse(success=success)
    
    # report failure if account doesn't exist and delete user otherwise
    def DeleteAccount(self, request, context):
        success = request.accountName in self.users
        if success:
            self.users.discard(request.accountName)
        return chat_pb2.DeleteAccountResponse(success=success)
    
    def ListAccounts(self, request, context):
        accounts = list(filter(lambda user: re.search(user, request.accountWildcard) != None, self.users))
        return chat_pb2.ListAccountsResponse(accounts=accounts)

    def Login(self, request, context):
        return chat_pb2.LoginResponse(success=request.accountName in self.users)
    
    def SendMessage(self, request, context):
        if request.accountName not in self.users:
            return chat_pb2.SendMessageResponse(success=False)
        else:
            # TODO: add locking for self.chats
            message = chat_pb2.SingleMessage(accountName=request.sender, message=request.message)
            self.chats[request.recipient].append(message)
            return chat_pb2.SendMessageResponse(success=True)

    # TODO: gonna have to figure out what happens when account is deleted mid message
    def ChatStream(self, request, context):
        user = request.acccountName
        while True:
            assert user in self.users, "user does not exist or no longer exists"
            # TODO: add locking for self.chats
            if self.chats[user]:
                yield self.chats[user].pop(0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
    