import os
import socket
if __name__ == '__main__':
    print(os.getcwd())

    # run the server file which is in the parent directory of this file
    os.system('python server.py')
    ip_addr = socket.gethostbyname(socket.gethostname())
    print("starting client at " + ip_addr)
    os.system('python client.py ' + ip_addr)
    # test creating an account
    
    # test deleting an account
    # test listing accounts
    # test logging in
    # test logging out
    # test sending a message
    # test receiving a message
