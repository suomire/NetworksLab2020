import socket
import sys
import datetime
import pytz
from tzlocal import get_localzone
import random
from custom_colors import Utils, colors
from message_utils import encode_message
import selectors

IP = "127.0.0.1"
PORT = 1234
HEADER_LEN = 10
my_username = input("Username: ")
WORK_SESSION = True
selector = selectors.DefaultSelector()
client_socket = None

fmt = '%Y-%m-%d %H:%M:%S'
local_tz = get_localzone()
username_colors = list(colors.values())


def set_client_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    events = selectors.EVENT_READ | selectors.EVENT_WRITE

    selector.register(fileobj=client_socket, events=events, data=listen_server)

    username = my_username.encode('utf-8')
    username_msg = f"{len(username):<{HEADER_LEN}}".encode('utf-8') + username
    client_socket.send(username_msg)


def transform_time_to_local_timezone(zone_line):
    usr_datetime = datetime.datetime.strptime(zone_line, fmt)
    utc_usr_datetime = usr_datetime.replace(tzinfo=pytz.utc)
    local_usr_time = utc_usr_datetime.astimezone(tz=local_tz)
    return local_usr_time.strftime(fmt)


def get_time_line():
    zone = datetime.datetime.now(tz=pytz.utc).strftime(fmt)
    return zone


def print_message(message):
    print(colors['DARKCYAN'] + message[0], '\t', end='')
    print(random.choice(username_colors) + Utils.BOLD + message[1] + Utils.END, ' > ', end='')
    print(colors['BLUE'] + message[2])


def message_processing(recv_message):
    msg = [m.decode('utf-8') for m in recv_message.split(b'\0')]
    if len(msg) == 1:
        print(colors['YELLOW'] + Utils.BOLD + msg[0] + colors['BLUE'] + Utils.END)
    else:
        msg[0] = transform_time_to_local_timezone(msg[0])
        print_message(msg)


def listen_server(client_socket):
    print('listen_server')
    try:
        message_header = client_socket.recv(HEADER_LEN)
        if not len(message_header):
            print("Connection closed by the server")
            print("Press any button to exit")
            WORK_SESSION = False
            sys.exit(0)

        message_len = int(message_header.decode('utf-8').strip())
        message = client_socket.recv(message_len)
        message_processing(message)

    except IOError as e:
        print('Reading error: {}'.format(str(e)))
        WORK_SESSION = False
        sys.exit(-1)


def send_server(client_socket):
    print('send server')
    message = input()
    if message and WORK_SESSION:
        msg = encode_message(message)
        msg = f'{len(msg):<{HEADER_LEN}}'.encode('utf-8') + msg
        client_socket.send(msg)


def event_clinet_loop():
    while True:
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj)


if __name__ == '__main__':
    set_client_socket()
    event_clinet_loop()
