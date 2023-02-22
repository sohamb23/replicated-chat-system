import os
import socket
#from ..chat_pb2 import *
# import the client class from the parent directory
from client import Client, PORT
import time
import sys
import threading
from io import StringIO

# set os to current directory
# launch the server python script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('python3 server.py &')                     # launch the server
time.sleep(1)                                        # wait for server to start
IP_ADDR = socket.gethostbyname(socket.gethostname()) # get ip address of server

class TestClient:
        
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP_ADDR, PORT))
    client = Client(s, IP_ADDR)                         # create a client object
    
    t1 = ''
    def test_create_account(self):
        response = self.client.CreateAccount('test1')
        assert response == True
        response = self.client.ListAccounts()
        assert response == ['test1']


    def test_create_conflicting_account(self):
        response = self.client.CreateAccount('test1')
        assert response == False
    
    def test_list_accounts(self):
        self.client.CreateAccount('test2')
        response = self.client.ListAccounts()
        assert sorted(response) == ['test1', 'test2']
    
    def test_list_accounts_by_wildcard(self):
        response = self.client.ListAccounts('1')
        assert response == ['test1']
        response = self.client.ListAccounts('test')
        assert sorted(response) == ['test1', 'test2']
    
    def test_multiple_creates(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_s:
            temp_s.connect((IP_ADDR, PORT))
            client2 = Client(temp_s, IP_ADDR)                   # create a new client object
            response = client2.CreateAccount('another')
            assert response == True
            response = client2.ListAccounts()
            assert sorted(response) == ['another', 'test1', 'test2'] # check that all clients can see each other's accounts
    
    
    def test_login(self):
        response = self.client.Login('test1')
        assert response == True
        assert self.client.username == 'test1'
    
    def test_login_with_nonexistent_account(self):
        response = self.client.Login('nonexistent')
        assert response == False
    
    def test_logout(self):
        self.client.Login('test1')
        response = self.client.Logout()
        assert response == True
        assert self.client.username == ''
    
    def test_delete(self):
        self.client.CreateAccount('test')
        self.client.Login('test')
        assert self.client.username == 'test'
        self.client.DeleteAccount()
        assert self.client.username == ''
        response = self.client.CreateAccount('test')
        assert response == True
    
    def test_delete_nonexistent_account(self):
        response = self.client.DeleteAccount()
        assert response == False
    
    def test_send_message(self):
        self.client.CreateAccount('test1')
        self.client.CreateAccount('test2')
        self.client.Login('test1')
        response = self.client.SendMessage('test2', 'hello')
        assert response == True                               # check that the message was sent


    def test_receive_message(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_s:
            temp_s.connect((IP_ADDR, PORT))
            client2 = Client(temp_s, IP_ADDR)                             # create a new client object
            client2.Login('test2')
            # redirect stdout to a variable
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            t1 = threading.Thread(target=client2.ListenForMessages)
            t1.start()
            time.sleep(1)
            sys.stdout = old_stdout
            output = mystdout.getvalue()
            assert output == '\n[test1]: hello\n'
    
    def test_send_message_to_nonexistent_account(self):
        self.client.CreateAccount('test1')
        self.client.Login('test1')
        response = self.client.SendMessage('nonexistent', 'hello')
        assert response == False
        self.client.Logout()
        self.s.close()