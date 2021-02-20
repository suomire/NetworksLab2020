import socket
import json
import threading
from math import sqrt, factorial

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


def get_answer(recv_request):
    if int(recv_request['opcode']) == OPCODE['+']:
        ans = recv_request['num1'] + recv_request['num2']
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    elif int(recv_request['opcode']) == OPCODE['-']:
        ans = recv_request['num1'] - recv_request['num2']
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    elif int(recv_request['opcode']) == OPCODE['*']:
        ans = recv_request['num1'] * recv_request['num2']
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    elif int(recv_request['opcode']) == OPCODE['/']:
        ans = recv_request['num1'] / recv_request['num2']
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    elif int(recv_request['opcode']) == OPCODE['!']:
        ans = factorial(recv_request['num'])
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    elif int(recv_request['opcode']) == OPCODE['sqrt']:
        ans = sqrt(recv_request['num'])
        answer = {'opcode': OPCODE['answer'], 'num': ans}
    return answer


def recv_send_request(sock, client_address):
    while True:
        try:
            recv_message = sock.recv(BLOCK_LENGTH).decode(CODE)
            if recv_message:
                recv_message = json.loads(recv_message)
                print(recv_message)
                answer = get_answer(recv_message)
                print(answer)
                json_request = json.dumps(answer).encode(CODE)
                sock.send(json_request)
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
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f'Listening for connections on {IP}:{PORT}...')
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address[0]}:{client_address[1]}")
        threading.Thread(target=recv_send_request, args=(client_socket, client_address)).start()


if __name__ == '__main__':
    main()
