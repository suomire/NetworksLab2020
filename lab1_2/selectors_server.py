import socket
import selectors
import sys
from message_utils import encode_message, message_processing

IP = "127.0.0.1"
# IP = "0.0.0.0"
PORT = 7556
HEADER_LEN = 10
SERVER_WORKING_SESSION = True
server_socket = None
client_names = {}
selector = selectors.DefaultSelector()  # epoll in linux
buffers_cs = dict()  # store client socket, len msg, gotten data


def set_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    server_socket.setblocking(False)

    selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_incoming_connection)

    print("Server is listening")


def broadcast(msg):
    """
    Send message to all chat users
    message is encoded
    """
    msg = f'{len(msg):<{HEADER_LEN}}'.encode('utf-8') + msg
    for client in client_names.keys():
        client.send(msg)


def close_server_socket():
    global client_names
    exit_msg = "Server stopped"
    exit_msg_header = f"{len(exit_msg):<{HEADER_LEN}}"
    exit_msg = exit_msg_header + exit_msg
    broadcast(exit_msg.encode('utf-8'))
    for c in client_names.keys():
        c.close()
        selector.unregister(c)
    client_names = {}
    server_socket.close()


def client_exit_from_chat(client_socket, name):
    send_messages(1, client_socket)
    client_socket.close()
    del client_names[client_socket]
    msg_bye = "%s has left the chat." % name
    selector.unregister(client_socket)
    broadcast(msg_bye.encode('utf-8'))


def send_messages(msg_type, client_socket, name=None):
    if msg_type == 0:  # welcome messages
        msg = "Welcome to chat!\n"
        msg = f"{len(msg):<{HEADER_LEN}}" + msg
        client_socket.send(msg.encode('utf-8'))

    elif msg_type == 1:  # exit messages
        exit_msg = "You exit from chat."
        exit_msg_header = f"{len(exit_msg):<{HEADER_LEN}}"
        exit_msg = exit_msg_header + exit_msg
        client_socket.send(exit_msg.encode('utf-8'))

    elif msg_type == 2:  # welcome info messages
        msg_welcome = "Hi, %s! To quit from chat type <quit< \n" % name
        msg_welcome = "Server >" + msg_welcome
        msg_welcome = f"{len(msg_welcome):<{HEADER_LEN}}" + msg_welcome
        client_socket.send(msg_welcome.encode('utf-8'))


def buffering_message(client_socket):
    global buffers_cs
    new_msg_len = buffers_cs[client_socket]['msg_len'] - len(buffers_cs[client_socket]['msg'])
    buffers_cs[client_socket]['msg'] += client_socket.recv(new_msg_len)

    if len(buffers_cs[client_socket]['msg']) == buffers_cs[client_socket]['msg_len']:
        msg = buffers_cs[client_socket]['msg']
        del buffers_cs[client_socket]
        return msg
    else:
        return False


def handle_client(client_socket):
    """
    Handling working with accepted client.
    1. Receiving client's name
    2. Sending info message
    3. Send broadcast message about new chat member
    4. Working with receiving new messages from this client

    """

    global buffers_cs
    msg = False
    try:
        if client_socket not in client_names.keys():
            name_header_len = int(client_socket.recv(HEADER_LEN).decode('utf-8').strip())
            name = client_socket.recv(name_header_len).decode('utf-8')
            client_names[client_socket] = name

            # send info message to client after getting his/her nickname
            send_messages(2, client_socket, name)

            msg_broadcast = "\t %s has joined to the chat! \n" % name
            broadcast(msg_broadcast.encode('utf-8'))

        else:
            # we get the message from client
            if client_socket in buffers_cs.keys():
                msg = buffering_message(client_socket)
            else:
                client_message = dict()
                msg_len = int(client_socket.recv(HEADER_LEN).decode('utf-8').strip())
                msg = client_socket.recv(msg_len)

                client_message['msg_len'] = msg_len
                client_message['msg'] = msg

                while len(msg) != msg_len:
                    try:
                        buffers_cs[client_socket] = client_message
                        msg += client_socket.recv(msg_len)
                        client_message['msg'] = msg

                    except BlockingIOError:
                        print('BlockingIOError occurred')
                        msg = False
                        break

        if msg:
            msg = message_processing(msg)

            if msg[2] != "<quit<":
                msg = encode_message(msg)
                broadcast(msg)
            else:
                client_exit_from_chat(client_socket, client_names[client_socket])

    except ValueError:
        print("Error occurred on the client's side")
        client_exit_from_chat(client_socket, client_names[client_socket])


def accept_incoming_connection(server_socket_arg):
    print('callback accept_incoming_connection')
    client_socket, client_address = server_socket_arg.accept()
    client_socket.setblocking(False)
    selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=handle_client)

    send_messages(0, client_socket)
    print("%s:%s has connected." % client_address)


def event_loop():
    try:
        while True:
            events = selector.select()  # (key, events)
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)
    except KeyboardInterrupt:
        print('\nYou stopped the server script')
        close_server_socket()
        sys.exit(0)


if __name__ == '__main__':
    set_server()
    event_loop()
