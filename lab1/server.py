import socket
from threading import Thread

IP = "127.0.0.1"
PORT = 1234
HEADER_LEN = 10
SERVER_WORKING_SESSION = True

server_socket = socket.socket(
    socket.AF_INET,  # family
    socket.SOCK_STREAM  # type
)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))  # localhost, port
server_socket.listen(5)

print("Server is listening")

clients = {}


def broadcast(msg, from_client=None):
    """
    Send message to all chat users
    msg in str!
    """
    msg_header = f"{len(msg):<{HEADER_LEN}}"
    msg = msg_header + msg

    for client in clients.keys():
        if (from_client is None) or client != from_client:
            client.send(msg.encode('utf-8'))


def handle_client(client):
    """
    Handling working with accepted clientself.
    1. Receiving client's name
    2. Sending info message
    3. Send broadcast message about new chat member
    4. Working with receiving new messages from this client

    """
    CLIENT_WORKING_SESSION = True
    global SERVER_WORKING_SESSION
    name_header_len = int(client.recv(HEADER_LEN).decode('utf-8').strip())
    name = client.recv(name_header_len).decode('utf-8')

    msg_welcome = "Hi, %s! To quit from chat type <quit< \n" % name
    msg_welcome = "Server >" + msg_welcome
    msg_welcome = f"{len(msg_welcome):<{HEADER_LEN}}" + msg_welcome

    client.send(msg_welcome.encode('utf-8'))

    msg_broadcast = "\t %s has joined to the chat! \n" % name
    broadcast(msg_broadcast, client)

    while CLIENT_WORKING_SESSION and SERVER_WORKING_SESSION:
        msg_len = int(client.recv(HEADER_LEN).decode('utf-8').strip())
        msg = client.recv(msg_len).decode('utf-8')

        print(msg)

        if msg.split(' > ')[-1] != "<quit<":
            broadcast(msg, client)
        else:
            exit_msg = "You exit from chat."
            exit_msg_header = f"{len(exit_msg):<{HEADER_LEN}}"
            exit_msg = exit_msg_header + exit_msg
            client.send(exit_msg.encode('utf-8'))
            client.close()
            del clients[client]
            msg_bye = "%s has left the chat." % name
            broadcast(msg_bye)
            CLIENT_WORKING_SESSION = False


def closing_listen():
    global SERVER_WORKING_SESSION
    while SERVER_WORKING_SESSION:
        message = input('Enter any message to close server << ')
        if message:
            SERVER_WORKING_SESSION = False
            exit_msg = "Server stoped"
            exit_msg_header = f"{len(exit_msg):<{HEADER_LEN}}"
            exit_msg = exit_msg_header + exit_msg
            broadcast(exit_msg)
            for c in clients.keys():
                c.close()
            server_socket.close()
            print('Server is closed')


def accept_incoming_connection():
    """
    Handling incoming connections:
    accept, send welcome message,
    add to client_dict, start a new thread
    """
    global SERVER_WORKING_SESSION
    closing_listen_thread = Thread(target=closing_listen)
    closing_listen_thread.start()
    while SERVER_WORKING_SESSION:
        if SERVER_WORKING_SESSION:
            client, client_address = server_socket.accept()
            print("%s:%s has connected." % client_address)
            msg = "Welcome to chat!\n"
            msg = f"{len(msg):<{HEADER_LEN}}" + msg
            client.send(msg.encode('utf-8'))

            clients[client] = client_address

            client_thread = Thread(target=handle_client, args=(client,))
            client_thread.start()


if __name__ == '__main__':
    accept_incoming_connection()
