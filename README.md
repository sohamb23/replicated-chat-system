# SimpleChat
A client/server application for a simple chat service. The first design project for CS 262 @ Harvard

## How to Use

### Preparation + Launching Server / Client
The user first clones this repository, then installs the required dependencies using `pip install -r requirements.txt`. Then, navigate to whichever part you want to run (part 1 is the socket implementation and part 2 is the gRPC implementation) launch run the server either in the background (`python server.py`) or in another terminal. Then run your client in another terminal using (`python client.py [server_ip]`). Note that after launching, the server will display the ip it is running on, which must be used as the argument for the script launching the client. 

### UI:
After you launch the client, you will be shown a menu with seven options:
1. Create Account
2. List all accounts
3. List account by wildcard
4. delete account
5. login
6. send message
7. logout + exit

The user then types a number specifying the option they want. After that, they specify the arguments. The client sends a message to the server, the server performs the requested action, and reports back the status of the request back to the client. The user can keep on specifying options as they please. Once the user is done, they can exit by typing 7

## Running Tests

You can test the client server interaction by navigating to either the `part1` or `part2` subdirectory and running `pytest test_part1.py` or `pytest test_part2.py` depending on which part you're testing. The test will simulate launching a server and client and report whether it can perform the essential functions.




