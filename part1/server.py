import socket, select

ip = '127.0.0.1'
port = 8080
header_length = 10

socket_list = []
users = {} #connected users - socket is the key and the username and data is the value

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket object
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #reuse address set to 1 on socket to avoid error
server_socket.bind((ip, port)) #bind socket to ip and port

server_socket.listen() #listen for connections
socket_list.append(server_socket) #add socket to socket_list

def receive_message(client_socket):
    # 
    try:
        message_header = client_socket.recv(header_length)

        if not len(message_header):
            return False
        
        message_length = int(message_header.decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False

while True:
    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], socket_list)

    for socketClient in read_sockets:
        if socketClient == server_socket:
            socketfd, socketaddr = server_socket.accept()
            user = receive_message(socketfd)

            if user is False:
                continue

            socket_list.append(socketfd)
            users[socketfd] = user
            print('Connected by', socketaddr)
        else:
            message = receive_message(socketClient)

            if message is False:
                print("Socket connection removed")
                socket_list.remove(socketClient)
                del users[socketClient]
                continue
                
            user = users[socketClient]
            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')

            for client in users:
                if client != socketClient:
                    client.send(user['header'] + user['data'] + message['header'] + message['data'])
            
    for socketClient in error_sockets:
        socket_list.remove(socketClient)
        del users[socketClient]



            # try:
            #     data = socketClient.recv(1024)
            #     if data.startswith("/quit"):
            #         sock.close()
            #         socket_list.remove(sock)
            #         del users[sock]
            #         continue
            #     if data.startswith("@"):
            #         users[data[1:].lower()] = sockfd
            #         sockfd.send("User added")
            #     else:
            #         for client_socket in socket_list:
            #             if client_socket != sock:
            #                 client_socket.send(data)
            # except ConnectionResetError:
            #     sock.close()
            #     socket_list.remove(sock)
            #     del users[sock]
            #     continue
server_socket.close()
