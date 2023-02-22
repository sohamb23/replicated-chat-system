import socket
import selectors
import types
import re
from threading import Lock, Thread
from collections import defaultdict, namedtuple

# selector for registering and managing connected sockets
sel = selectors.DefaultSelector()
# type for messages
SingleMessage = namedtuple("SingleMessage", ["sender", "message"])

IP_ADDR = socket.gethostbyname(socket.gethostname()) # get ip address of server
PORT = 50051

# Non GRPC implementation
class Server():

    # initialize the server with empty users, chats, and online lists
    def __init__(self):
        self.users_lock = Lock() # lock for both self.users and self.online
        self.users = set()
        self.chat_locks = defaultdict(lambda: Lock()) # locks for each k, v pair in self.chats
        self.chats = defaultdict(lambda: [])
        self.online = set()

    # report failure if account already exists and add user otherwise
    def CreateAccount(self, user):
        with self.users_lock:
            success = user not in self.users
            if success:
                print("adding user: " + user)
                self.users.add(user)
        return success
    
    # report failure if account doesn't exist and delete user otherwise
    def DeleteAccount(self, user):
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
        return success
    
    # report failure if account doesn't exist and return list of accounts that match wildcard otherwise
    def ListAccounts(self, accountWildcard):
        # search in users for accounts that match wildcard
        pattern = re.compile(accountWildcard)
        with self.users_lock:
            accounts = list(filter(lambda user: pattern.search(user) != None, self.users))
        print("listing users: " + str(accounts))
        return accounts

    # report failure if account doesn't exist and add user to online list otherwise
    def Login(self, user):
        print("logging in user: " + user)
        with self.users_lock:
            self.online.add(user)
            success = user in self.users
        return success

    # report failure if account doesn't exist and remove user from online list otherwise
    def Logout(self, user):
        print("logging out user: " + user)
        with self.users_lock:
            success = user in self.online
            self.online.discard(user)
        return success

    # report failure if recipient doesn't exist and send message otherwise
    def SendMessage(self, sender, recipient, message):
        print(f"received message from {sender} to {recipient}: {message}")
        self.users_lock.acquire(blocking=True)
        if recipient not in self.users:
            self.users_lock.release()
            return False
        else:
            self.users_lock.release()
            message = SingleMessage(sender, message)
            with self.chat_locks[recipient]:
                self.chats[recipient].append(message)
            return True

    # report failure if account doesn't exist and start chat stream otherwise
    def ChatStream(self, user, data_stream):
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
                    msg = self.chats[user].pop(0)
                    data_stream.outb += str(msg).encode("utf-8")
            # reacquire lock before checking while condition
            self.users_lock.acquire(blocking=True)
        # release lock before stopping stream
        self.users_lock.release()

# methods that will be exposed to the client; our analog to services
SERVER_METHODS = list(filter(lambda x: x[:2] != "__", dir(Server)))
STREAM_CODE = 50 # designated integer code with a high value to avoid clashes with other method codes
# run a method on the server given a code for the method and a tuple of the args to pass in
def run_server_method(method_code, args, server: Server):
    return getattr(server, SERVER_METHODS[method_code])(*args)

# a wrapper function for accepting sockets with some additional configuration
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

# service a socket that is connected: handle inbound and outbound data
# while running any necessary chat server methods
def service_connection(key, mask, server: Server):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            method_code, args = eval(recv_data.decode("utf-8"))
            if method_code != STREAM_CODE:
                output = run_server_method(method_code, args, server)
                data.outb += str(output).encode("utf-8")
            else:
                # start up the thread and pass the data object, so the thread can write to it
                t = Thread(target=server.ChatStream, args=(*args, data))
                t.start()
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            # handle outbound data
            sock.sendall(data.outb)
            data.outb = b''

# start the server
def serve():
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((IP_ADDR, PORT))
    lsock.listen()
    print(f"Listening on {(IP_ADDR, PORT)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    server = Server()

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask, server)

# run the server when this script is executed
if __name__ == '__main__':
    serve()