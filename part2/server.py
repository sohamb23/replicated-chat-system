import grpc
import chat_pb2
import chat_pb2_grpc
import re
import sys
from concurrent import futures
from threading import Lock, Thread
import socket
from collections import defaultdict
import time
import csv
import os

# Server class that implements the ChatServicer interface defined by proto file.
# This class is responsible for handling the RPC calls from the client.

# server addrs for my machine
SERVER_ADDRS = {1: "10.250.147.180:50051", 2: "10.250.147.180:50052", 3: "10.250.147.180:50053"}

# multiple server addrs:
# SERVER_ADDRS = {1: "10.250.11.129:50051", 2: "10.250.11.129:50052", 3: "10.250.11.129:50053", 4: "10.250.147.180:50051", 5: "10.250.147.180:50052", 6: "10.250.147.180:50053"}

FILE_PATH = "ACTION_LOG.csv"


# 10.250.147.180:50051

## server addrs for multiple machines
#TODO: SERVER_ADDRS_MULTIPLE: add server addrs for multiple machines

class ChatServicer(chat_pb2_grpc.ChatServicer):

    # initialize the server with empty users, chats, and online lists
    def __init__(self, id):
        self.users_lock = Lock() # lock for both self.users and self.online
        self.users = set()
        self.chat_locks = defaultdict(lambda: Lock()) # locks for each k, v pair in self.chats
        self.chats = defaultdict(lambda: [])
        self.online = set()
        self.server_addrs = SERVER_ADDRS
        self.primary_id = None
        self.id = int(id)
        self.methodMap = {"CreateAccount": "CreateAccountRequest", "DeleteAccount": "DeleteAccountRequest", "Login": "LoginRequest", "Logout": "LogoutRequest", "SendMessage": "MessageSendRequest"}
        if(os.path.exists(FILE_PATH)):
            # self.log = open(FILE_PATH, "a+")
            # self.writer = csv.writer(self.log) 
            reader = csv.reader(open(FILE_PATH, "r"))
            for row in reader:
                clientMethod = self.methodMap[row[0]]
                # args = row[1:-1]
                if clientMethod != "MessageSendRequest":
                    getattr(self, row[0])(getattr(chat_pb2, self.methodMap[row[0]])(accountName = row[1]), row[-1])
                else:
                    getattr(self, row[0])(getattr(chat_pb2, self.methodMap[row[0]])(sender = row[1], recipient = row[2], message = row[3]), row[-1])
        else:
            with open(FILE_PATH, "a+") as f:
                f.close()
            # self.writer = csv.writer(self.log)
           

        # with self.log as f:
            # self.writer.writerow(["Action", "Request", "Context"])

        # self.writer.writerow(["Action", "Request", "Context"])
                # self.writer.writerow(["timestamp", "sender", "recipient", "message"])
        # with open("action_log.csv", "r") as f:
        #     reader = csv.reader(f)
        #     for row in reader:

        #         self.action_log.append(row)
        self.action_log = []
        # self.CreateAccount("")
        time.sleep(5)
        self.election_thread = Thread(target=self.ElectLeader)
        self.election_thread.start()
        

    # report failure if account already exists and add user otherwise
    def CreateAccount(self, request, context):
        user = request.accountName
        with self.users_lock:
            success = user not in self.users
            if success:
                print("adding user: " + user)
                self.users.add(user)
        print(request)
        print(type(request))
        # with open(FILE_PATH, "w") as f:
        with open(FILE_PATH, "a+") as f:
            if(self.primary_id == self.id):
                writer = csv.writer(f)
                writer.writerow(["CreateAccount", request.accountName, context])
            f.close()
        # if(self.primary_id == self.id):
        #     self.writer.writerow(["CreateAccount", request, context])
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
                    if user in self.chats:
                        del self.chats[user] # delete undelivered chats if you are deleting the account
                del self.chat_locks[user]
        with open(FILE_PATH, "a+") as f:
            if(self.primary_id == self.id):
                writer = csv.writer(f)
                writer.writerow(["DeleteAccount", request.accountName, context])
            f.close()
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
        with open(FILE_PATH, "a+") as f:
            if(self.primary_id == self.id):
                writer = csv.writer(f)
                writer.writerow(["Login", request.accountName, context])
            f.close()
        return chat_pb2.LoginResponse(success=success)

    # report failure if account doesn't exist and remove user from online list otherwise
    def Logout(self, request, context):
        user = request.accountName
        print("logging out user: " + user)
        with self.users_lock:
            success = user in self.online
            self.online.discard(user)
        with open(FILE_PATH, "a+") as f:
            if(self.primary_id == self.id):
                writer = csv.writer(f)
                writer.writerow(["Logout", request.accountName, context])
            f.close()
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
            with open(FILE_PATH, "a+") as f:
                if(self.primary_id == self.id):
                    writer = csv.writer(f)
                    writer.writerow(["SendMessage", request.sender, request.recipient, request.message, context])
                f.close()
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
    
    def GetServerId(self, request, context):
        return chat_pb2.GetServerIdResponse(serverId=self.id)
    
    def UpdatePrimaryServer(self, request, context):
        self.primary_id = int(request.primaryServerId)
        print(str(self.id) + ": NEW PRIMARY SERVER: " + self.server_addrs[self.primary_id])
        return chat_pb2.UpdatePrimaryServerResponse(success=True)
    
    # constantly run this function make sure that the primary server is 
    # always the active server with the lowest id
    def ElectLeader(self):
        while True:
            min_id = self.id
            for id in self.server_addrs:
                if id != self.id:
                    # try to establish connection with server, handle if it fails
                    try:
                        with grpc.insecure_channel(self.server_addrs[id]) as channel:
                            stub = chat_pb2_grpc.ChatStub(channel)
                            response = stub.GetServerId(chat_pb2.Empty())
                            if int(response.serverId) < min_id:
                                min_id = int(response.serverId)
                    except:
                        print(str(self.id) + ": failed to connect to server " + self.server_addrs[id])
            
            if self.primary_id  != min_id:
                self.primary_id = min_id
                print(str(self.id) + ": NEW PRIMARY SERVER: " + self.server_addrs[self.primary_id])
                # Update the primary server for all of the other servers
                for id in self.server_addrs:
                    if id != self.id:
                        try:
                            with grpc.insecure_channel(self.server_addrs[id]) as channel:
                                stub = chat_pb2_grpc.ChatStub(channel)
                                stub.UpdatePrimaryServer(chat_pb2.UpdatePrimaryServerRequest(primaryServerId=self.primary_id))
                        except:
                            print(str(self.id) + ": failed to connect to server " + self.server_addrs[id])
            time.sleep(1)
        


# start the server
def serve(port, id):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(id), server) 

    ip_address = socket.gethostbyname(socket.gethostname()) # get ip address of server
    server.add_insecure_port(ip_address + ':' + port)         # add port to ip address

    print("starting server at " + ip_address + ':' + port)
    server.start()
    server.wait_for_termination()

# run the server when this script is executed
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python3 server.py <port> <id>")
        exit()
    else:
        port = sys.argv[1]
        id = sys.argv[2]
        serve(port, id)
    