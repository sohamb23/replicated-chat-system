import os
import socket
#from ..chat_pb2 import *
# import the client class from the parent directory
from client import Client
import time

# set os to current directory
# launch the server python script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.system('python3 server.py &')
time.sleep(1) # wait for server to start

class TestClient:
    client = Client()
        
    def test_create_account(self):
        response = self.client.CreateAccount('test1')
        assert response == True

    def test_create_conflicting_account(self):
        response = self.client.CreateAccount('test1')
        assert response == False
    
    def test_list_accounts(self):
        response = self.client.ListAccounts()
        assert response == ['test1']
    
    def test_list_accounts_by_wildcard(self):
        response = self.client.ListAccounts('1')
        assert response == ['test1']
    
    def test_login(self):
        response = self.client.Login('test1')
        assert response == True
    
    def test_login_with_nonexistent_account(self):
        response = self.client.Login('test2')
        assert response == False
    
    def test_logout(self):
        self.client.Login('test1')
        response = self.client.Logout()
        assert response == True
        assert self.client.username == ''
    
    def test_delete_nonexistent_account(self):
        response = self.client.DeleteAccount()
        assert response == False
    
    def test_send_message(self):
        self.client.CreateAccount('test1')
        self.client.CreateAccount('test2')
        self.client.Login('test1')
        response = self.client.SendMessage('test2', 'hello')
        assert response == True
    
    def cleanup():
        os.system('pkill -f server.py')