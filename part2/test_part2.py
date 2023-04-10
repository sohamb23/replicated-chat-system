import os
import socket
#from ..chat_pb2 import *
# import the client class from the parent directory
from client import Client
import time
import sys
import threading
from io import StringIO
from multiprocessing import Process
import server

# set os to current directory
# launch the server python script
# DELETE ACTION_LOG.CSV
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system("rm ACTION_LOG.csv")
IP_ADDR = socket.gethostbyname(socket.gethostname()) # get ip address of server
p1 = Process(target=server.serve, args=('50051', '1'))
p2 = Process(target=server.serve, args=('50052', '2'))
p3 = Process(target=server.serve, args=('50053', '3'))
p1.start()
p2.start()
p3.start()
time.sleep(5)                                         # wait for server to start


class TestClient:
        
    client = Client(IP_ADDR + ":50051")                         # create a client object
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
        p1.terminate()                                           # kill first server
        time.sleep(5)
    
    def test_multiple_creates(self):
        client2 = Client(IP_ADDR + ":50052")                     # create a new client object
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
        p2.terminate()                                        # kill second server
        time.sleep(5)



    def test_receive_message(self):
        client2 = Client(IP_ADDR + ":50053")                  # create a new client object
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
        self.client.stop_listening = True
    
    def test_send_message_to_nonexistent_account(self):
        self.client.CreateAccount('test1')
        self.client.Login('test1')
        response = self.client.SendMessage('nonexistent', 'hello')
        assert response == False
        self.client.Logout()
        
# exit pytest