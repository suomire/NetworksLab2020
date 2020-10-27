import socket
import threading
import sys
import datetime
import pytz
from tzlocal import get_localzone
from time import sleep
import random
from custom_colors import Utils, colors

IP = "51.15.130.137"
# IP = "127.0.0.1"
PORT = 7556
HEADER_LEN = 10
my_username = input("Username: ")
WORK_SESSION = True

fmt = '%Y-%m-%d %H:%M:%S'
local_tz = get_localzone()
username_colors = list(colors.values())

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
client_socket.connect((IP, PORT))

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
        print(colors['RED'] + Utils.BOLD + msg[0] + colors['BLUE'] + Utils.END)
    else:
        msg[0] = transform_time_to_local_timezone(msg[0])
        print_message(msg)


def listen_server():
    global WORK_SESSION
    while WORK_SESSION:
        try:
            message_header = client_socket.recv(HEADER_LEN)
            if not len(message_header):
                print("Connection closed by the server")
                print("Press any button to exit")
                WORK_SESSION = False
                sys.exit(0)

            message_len = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_len)
            while len(message) != message_len:
                message += client_socket.recv(message_len)
            message_processing(message)

        except IOError as e:
            print('Reading error: {}'.format(str(e)))
            WORK_SESSION = False
            sys.exit(-1)
            continue


def encode_message(message):
    timeline = get_time_line().encode('utf-8')
    usr = my_username.encode('utf-8')
    msg = message.encode('utf-8')
    return b'\0'.join([timeline, usr, msg])


def send_server():
    listen_thread = threading.Thread(target=listen_server)
    listen_thread.daemon = True
    listen_thread.start()
    sleep(1)
    while WORK_SESSION:
        try:
            message = input()
            if message and WORK_SESSION:
                msg = encode_message(message)
                msg = f'{len(msg):<{HEADER_LEN}}'.encode('utf-8') + msg
                client_socket.send(msg)
        except KeyboardInterrupt:
            print('\nYou closed client script')
            sys.exit(0)


if __name__ == '__main__':
    send_server()
