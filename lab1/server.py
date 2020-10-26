import socket
from threading import Thread
import sys

IP = "127.0.0.1"
# IP = "0.0.0.0"
PORT = 7556
HEADER_LEN = 10
SERVER_WORKING_SESSION = True
_FINISH = False

server_socket = socket.socket(
    socket.AF_INET,  # family
    socket.SOCK_STREAM  # type
)
# использовать повторно созданный выше сокет
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))  # localhost, port
server_socket.listen()

print("Server is listening")

clients = {}


def broadcast(msg):
    """
    Send message to all chat users
    message is encoded
    """
    msg = f'{len(msg):<{HEADER_LEN}}'.encode('utf-8') + msg
    for client in clients.keys():
        client.send(msg)


def encode_message(message):
    timeline = message[0].encode('utf-8')
    username = message[1].encode('utf-8')
    msg_content = message[2].encode('utf-8')
    msg = b'\0'.join([timeline, username, msg_content])
    return msg


def message_processing(message):
    msg = [m.decode('utf-8') for m in message.split(b'\0')]
    return msg


def client_exit_from_chat(client, name):
    exit_msg = "You exit from chat."
    exit_msg_header = f"{len(exit_msg):<{HEADER_LEN}}"
    exit_msg = exit_msg_header + exit_msg
    client.send(exit_msg.encode('utf-8'))
    client.close()
    del clients[client]
    msg_bye = "%s has left the chat." % name
    broadcast(msg_bye.encode('utf-8'))


def send_welcome_message(client, name):
    msg_welcome = "Hi, %s! To quit from chat type <quit< \n" % name
    msg_welcome = "Server >" + msg_welcome
    msg_welcome = f"{len(msg_welcome):<{HEADER_LEN}}" + msg_welcome
    client.send(msg_welcome.encode('utf-8'))


def handle_client(client):
    """
    Handling working with accepted client.
    1. Receiving client's name
    2. Sending info message
    3. Send broadcast message about new chat member
    4. Working with receiving new messages from this client

    """
    client_working_session = True
    global SERVER_WORKING_SESSION
    name_header_len = int(client.recv(HEADER_LEN).decode('utf-8').strip())
    name = client.recv(name_header_len).decode('utf-8')

    send_welcome_message(client, name)

    msg_broadcast = "\t %s has joined to the chat! \n" % name
    broadcast(msg_broadcast.encode('utf-8'))
    while client_working_session and SERVER_WORKING_SESSION:
        try:
            msg_len = int(client.recv(HEADER_LEN).decode('utf-8').strip())
            msg = client.recv(msg_len)
            if len(msg) == msg_len:
                msg = message_processing(msg)
                
            if msg[2] != "<quit<":
                msg = encode_message(msg)
                broadcast(msg)
            else:
                client_exit_from_chat(client, name)
                client_working_session = False

        except ValueError as e:
            print(e)
            print("Error occurred on the client's side")
            client_working_session = False
            client_exit_from_chat(client, name)

    print('Thread for ', name, ' stopped')


def close_all_threads():
    for c in client_threads:
        c.join()
    print('All client threads are closed')


def close_server_socket():
    global clients
    exit_msg = "Server stopped"
    broadcast(exit_msg.encode('utf-8'))
    for c in clients.keys():
        c.close()
    clients = {}
    server_socket.close()


def accept_incoming_connection():
    """
    Handling incoming connections:
    accept, send welcome message,
    add to client_dict, start a new thread
    """
    global SERVER_WORKING_SESSION, client_threads
    try:
        while SERVER_WORKING_SESSION:
            # blocking operation....
            client, client_address = server_socket.accept()
            print("%s:%s has connected." % client_address)
            msg = "Welcome to chat!\n"
            msg = f"{len(msg):<{HEADER_LEN}}" + msg
            client.send(msg.encode('utf-8'))

            clients[client] = client_address
            client_thread = Thread(target=handle_client, args=(client,))
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        # in case of closing server with active connections
        SERVER_WORKING_SESSION = False
        if len(clients) != 0:
            close_server_socket()
        # in case of correct closing server
        print('\nYou stopped the server')
        sys.exit(0)


if __name__ == '__main__':
    accept_incoming_connection()
