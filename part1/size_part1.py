from server import SERVER_METHODS
import sys

user = "Alan Turing"
wildcard = "Tu"
sender = user
recipient = "Alonzo Church"
message = "Hi, my name is Alan."
trials = [
    ("CreateAccount", (user,)),
    ("DeleteAccount", (user,)),
    ("ListAccounts", (wildcard,)),
    ("Login", (user,)),
    ("Logout", (user,)),
    ("SendMessage", (sender, recipient, message)),
    ("ChatStream", (user,))
]

for method, args in trials:
    method_code = SERVER_METHODS.index(method)
    transmission = str((method_code, args)).encode("utf-8")
    print(f"{method}: {sys.getsizeof(transmission)}")