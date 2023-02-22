import os
import socket
# import the client class from the parent directory
from client import Client, PORT
import time
import sys

# set os to current directory
# launch the server python script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('python3 server.py &')                     # launch the server
time.sleep(1)                                        # wait for server to start
IP_ADDR = socket.gethostbyname(socket.gethostname()) # get ip address of server

def one_sequence():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP_ADDR, PORT))
        client = Client(s, IP_ADDR)                         # create a client object

        for i in range(10):
            client.CreateAccount(f'test{i}')
            client.ListAccounts()
            client.ListAccounts('1')
        for i in range(10):
            client.CreateAccount(f'test{i}')
        client.Login('test0')
        for i in range(100):
            client.SendMessage('test1', 'ayo my guy wuts good')
        client.Logout()
        client.Login('test1')
        # after test1 logins, they'll begin to receive messages but the chatstream thread
        # would be hindered by another thread trying to acquire the users_lock
        # this list account command will want users_lock which should delay the chatstream thread
        for i in range(10):
            client.ListAccounts('1')
        client.Logout()
        for i in range(10):
            client.Login(f'test{i}')
            client.Logout()
        for i in range(10):
            client.Login(f'test{i}')
            client.DeleteAccount()

def run(i):
    times = []
    for _ in range(i):
        start = time.time()
        one_sequence()
        stop = time.time()
        times.append(stop - start)
    return times

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please pass the number of times to run the sequence as an argument")
    else:
        print(run(int(sys.argv[1])))
