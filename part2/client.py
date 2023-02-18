import chat_pb2
import chat_pb2_grpc
import grpc
import threading


def listen_for_messages(stub, username):
    for msg in stub.ChatStream(chat_pb2.ChatRequest(accountName=username)):
        print()
        print("[" + msg.sender + "]: " + msg.message)

# runs the client and allows user to select rpc calls
def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chat_pb2_grpc.ChatStub(channel)
        print('1. Create Account')
        print('2. List All Accounts')
        print('3. List Account by Wildcard')
        print('4. Delete Account')
        print('5. Login')
        print('6. Send Message')
        print('7. Exit')
        user_input = input("Enter option: ")   # ask user for which option they want
        if user_input in ['1', '2', '3', '4', '5', '6', '7']:
            rpc_call = int(user_input)
        else:
            rpc_call = 0
        usr = ''                                             # the name of the user (initialized to empty string)
        while rpc_call != 7:
            # Creating an account
            if rpc_call == 1:
                username = input('Enter username that you want to create: ')
                response = stub.CreateAccount(chat_pb2.CreateAccountRequest(accountName=username))
                print("Account Created Successfully" if response.success else "Account Creation Failed")
            # List all accounts
            elif rpc_call == 2:
                response = stub.ListAccounts(chat_pb2.ListAccountsRequest(accountWildcard = '.*'))
                for account in response.accounts:
                    print(account)
            # List accounts by wildcard
            elif rpc_call == 3:
                wildcard = input('Enter wildcard: ')
                response = stub.ListAccounts(chat_pb2.ListAccountsRequest(accountWildcard=wildcard))
                for account in response.accounts:
                    print(account)
            elif rpc_call == 4:
                username = input('Enter username for deletion: ')
                response = stub.DeleteAccount(chat_pb2.DeleteAccountRequest(accountName=username))
                print('Account deleted' if response.success else 'Account deletion failed')
            # Login and set up stream for messages
            elif rpc_call == 5:
                username = input('Enter username: ')
                response = stub.Login(chat_pb2.LoginRequest(accountName=username))
                if response.success:
                    usr = username
                    print("Login successful. Unread and new incoming messages will be shown below...")
                    threading.Thread(target=listen_for_messages, args=(stub, username)).start()
                else:
                    print("Login failed")
            # Send Message
            elif rpc_call == 6:
                if usr == '':
                    print('You must log in to send a message')
                else:
                    username = input('Enter username you want to send to: ')
                    msg = input('Enter message: ')
                    response = stub.SendMessage(chat_pb2.MessageSendRequest(recipient=username, sender=usr, message=msg))
                    print("Message sent" if response.success else "Message failed to send")
            else:
                print('Invalid option')
            user_input = input("Enter option: ")   # ask user for which option they want
            if user_input in ['1', '2', '3', '4', '5', '6', '7']:
                rpc_call = int(user_input)
            else:
                rpc_call = 0
        if usr != '':
            response = stub.Logout(chat_pb2.LogoutRequest(accountName=usr))
        print('Exiting...')
if __name__ == '__main__':
    run()