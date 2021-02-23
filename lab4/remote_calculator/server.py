import socket
import json
import threading
from math import sqrt, factorial
import time
from threading import Thread

IP = "0.0.0.0"
PORT = 5454
CODE = 'utf-8'
BLOCK_LENGTH = 512

OPCODE = {
    '+': 0,
    '-': 1,
    '*': 2,
    '/': 3,
    '!': 4,
    'sqrt': 5,
    'answer': 6
}

client_sockets = []


def long_calculations(recv_request, sock):
    time.sleep(10)
    if recv_request['opcode'] == OPCODE['!']:
        ans = factorial(recv_request['num'])
    elif recv_request['opcode'] == OPCODE['sqrt']:
        ans = sqrt(recv_request['num'])

    answer = {'opcode': OPCODE['answer'], 'num': ans, 'id': recv_request['id']}
    print(answer)
    json_request = json.dumps(answer).encode(CODE)
    sock.send(json_request)


def get_answer(recv_request):
    if recv_request['op_type'] == 1:
        if recv_request['opcode'] == OPCODE['+']:
            ans = recv_request['num1'] + recv_request['num2']
        elif recv_request['opcode'] == OPCODE['-']:
            ans = recv_request['num1'] - recv_request['num2']
        elif recv_request['opcode'] == OPCODE['*']:
            ans = recv_request['num1'] * recv_request['num2']
        elif recv_request['opcode'] == OPCODE['/']:
            ans = recv_request['num1'] / recv_request['num2']

        answer = {'opcode': OPCODE['answer'], 'num': ans, 'id': recv_request['id']}
        return answer


def recv_send_request(sock, client_address):
    while True:
        try:
            recv_message = sock.recv(BLOCK_LENGTH).decode(CODE)
            if recv_message:
                recv_message = json.loads(recv_message)
                print(recv_message)
                if recv_message['op_type'] == 1:
                    answer = get_answer(recv_message)
                    print(answer)
                    json_request = json.dumps(answer).encode(CODE)
                    sock.send(json_request)
                else:
                    Thread(target=long_calculations, args=(recv_message, sock), daemon=True).start()
            else:
                print(f'Closed connection from: {client_address}')
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                return
        except ConnectionResetError:
            print(f'Closed connection from: {client_address}')
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return


def main():
    global client_sockets
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f'Listening for connections on {IP}:{PORT}...')
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_sockets.append(client_socket)
            print(f"New connection from {client_address[0]}:{client_address[1]}")
            threading.Thread(target=recv_send_request, args=(client_socket, client_address), daemon=True).start()
    except:
        for cs in client_sockets:
            cs.close()
        server_socket.close()
        print('Server is closed')


if __name__ == '__main__':
    main()
