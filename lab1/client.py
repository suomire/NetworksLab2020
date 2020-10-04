import socket
import threading
import sys
import datetime
import pytz
from tzlocal import get_localzone
from time import sleep

HEADER_LEN = 10
my_username = input("Username: ")
WORK_SESSION = True

fmt = '%Y-%m-%d %H:%M:%S&&&'
fmt_print = '%Y-%m-%d %H:%M:%S'
local_tz = get_localzone()

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
client_socket.connect(("127.0.0.1", 1234))

username = my_username.encode('utf-8')
username_msg = f"{len(username):<{HEADER_LEN}}".encode('utf-8') + username
client_socket.send(username_msg)


def transform_time_to_local_timezone(zone_line):
    usr_datetime = datetime.datetime.strptime(zone_line, fmt_print)
    utc_usr_datetime = usr_datetime.replace(tzinfo=pytz.utc)
    local_usr_time = utc_usr_datetime.astimezone(tz=local_tz)
    return local_usr_time


def get_time_line():
    zone = datetime.datetime.now(tz=pytz.utc).strftime(fmt)
    return zone


def get_transformed_message(message):
    time, message = message.split("&&&")[0], message.split("&&&")[-1]
    if time == message:
        return message
    else:
        time = transform_time_to_local_timezone(time)
        message = time.strftime(fmt_print) + " " + message
        return message


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
            message = client_socket.recv(message_len).decode('utf-8')
            message = get_transformed_message(message)

            print(message)

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                sys.exit(-1)
                continue


def send_server():
    listen_thread = threading.Thread(target=listen_server)
    listen_thread.start()
    sleep(1)
    while WORK_SESSION:
        message = input(f'{my_username} << ')
        if message:
            message = get_time_line() + '\t' + my_username + ' > ' + message
            message = f'{len(message):<{HEADER_LEN}}' + message
            client_socket.send(message.encode('utf-8'))


if __name__ == '__main__':
    send_server()
