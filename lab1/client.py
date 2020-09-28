import socket
import threading

HEADER_LEN = 10
my_username = input("Username: ")

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

client_socket.connect(("127.0.0.1", 1236))

username = my_username.encode('utf-8')
username_msg = f"{len(username):<{HEADER_LEN}}".encode('utf-8') + username
client_socket.send(username_msg)


def listen_server():
    while True:
        try:

            message_header = client_socket.recv(HEADER_LEN)
            if not len(message_header):
                print("Connection closed by the server")
                sys.exit()

            message_len = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_len).decode('utf-8')

            print(message)

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                sys.exit()

                continue

def send_server():
    listen_thread = threading.Thread(target=listen_server)
    listen_thread.start()
    while True:
        message = input(f'{my_username} << \n')
        if message:
            message = my_username +' > ' + message
            message = f'{len(message):<{HEADER_LEN}}' + message
            client_socket.send(message.encode('utf-8'))


if __name__ == '__main__':
    send_server()
