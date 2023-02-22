import sys
import chat_pb2

user = "Alan Turing"
wildcard = "Tu"
sender = user
recipient = "Alonzo Church"
message = "Hi, my name is Alan."
trials = [
    ("CreateAccount", chat_pb2.CreateAccountRequest(accountName=user)),
    ("DeleteAccount", chat_pb2.DeleteAccountRequest(accountName=user)),
    ("ListAccounts", chat_pb2.ListAccountsRequest(accountWildcard = wildcard)),
    ("Login", chat_pb2.LoginRequest(accountName=user)),
    ("Logout", chat_pb2.LogoutRequest(accountName=user)),
    ("SendMessage", chat_pb2.MessageSendRequest(sender=sender, recipient=recipient, message=message)),
    ("ChatStream", chat_pb2.ChatRequest(accountName=user))
]

for method, request in trials:
    print(f"{method}: {sys.getsizeof(request)}")
