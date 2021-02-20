import random
import socket
import psycopg2
import json
import threading

"""
Written by Nikolay Koknov, 70202
"""


for_conn = open("connection.txt", 'r').readlines()[0].split(" ")

IP = "0.0.0.0"
PORT = 5454
CODE = 'utf-8'
BLOCK_LENGTH = 10

OPCODE = {
    'Register': 0,
    'Sign in': 1,
    'Other wallets': 2,
    'Transaction': 3,
    'Sum': 4,
    'Answer': 5
}

users = {}
client_sockets = []

connection = psycopg2.connect(user=for_conn[0], password=for_conn[1], database=for_conn[2],
                              host=for_conn[3], port=for_conn[4])
cursor = connection.cursor()


def client_connect(sock):
    client_socket, client_address = sock.accept()
    client_sockets.append(client_socket)
    print(f"New connection from {client_address[0]}:{client_address[1]}")
    return client_socket, client_address


def new_wallet_number():
    wallet_num = ''.join([random.choice('1234567890') for _ in range(12)])
    while True:
        cursor.execute('SELECT id FROM \"user\" WHERE wallet_number = ' + str(wallet_num))
        if cursor.fetchall():
            wallet_num = ''.join([random.choice('1234567890') for _ in range(12)])
        else:
            return wallet_num


def registration(address, name, password):
    wallet_num = new_wallet_number()
    cursor.execute("INSERT INTO \"user\" VALUES (default, %s, md5(%s), %s, 5000)", (name, password, wallet_num))
    users[address] = wallet_num
    connection.commit()
    return wallet_num


def sign_in(address, name, password):
    cursor.execute('SELECT wallet_number FROM \"user\" WHERE username = %s AND password = md5(%s)', (name, password))
    wallet_num = cursor.fetchall()
    if wallet_num:
        users[address] = wallet_num[0][0]
        return wallet_num[0][0]
    else:
        return False


def get_sum(address):
    wallet_num = users[address]
    cursor.execute('SELECT sum FROM \"user\" WHERE wallet_number = %s', (wallet_num,))
    sum = cursor.fetchall()
    return sum[0][0]


def transaction(address, enemy_wallet_num, sum_transaction):
    wallet_num = users[address]
    current_sum = get_sum(address)
    if int(current_sum) < int(sum_transaction):
        return False
    else:
        cursor.execute('UPDATE \"user\" SET sum = sum - %s WHERE wallet_number = %s',
                       (sum_transaction, wallet_num))
        cursor.execute('UPDATE \"user\" SET sum = sum + %s WHERE wallet_number = %s',
                       (sum_transaction, enemy_wallet_num))
        connection.commit()
        return True


def get_other_wallets(address):
    wallet_num = users[address]
    cursor.execute('SELECT username, wallet_number FROM \"user\" WHERE wallet_number != %s', (wallet_num,))
    sum = cursor.fetchall()
    return sum


def receive_message(sock):
    try:
        message_header = sock.recv(BLOCK_LENGTH)
        if not len(message_header):
            return False

        message_length = int(message_header.decode(CODE))
        message = b""
        while message_length != len(message):
            message += sock.recv(message_length - len(message))
        return {'header': message_header, 'data': message}
    except:
        return False


def recv_request(sock, client_address):
    while True:
        try:
            recv_message = receive_message(sock)
            if recv_message:
                recv_message = json.loads(recv_message['data'].decode(CODE))
                answer = False
                if recv_message['opcode'] == OPCODE['Register']:
                    print(f'Client {client_address} want to register')
                    answer = registration(client_address, recv_message['name'], recv_message['password'])
                elif recv_message['opcode'] == OPCODE['Sign in']:
                    print(f'Client {client_address} want to sign in')
                    answer = sign_in(client_address, recv_message['name'], recv_message['password'])
                elif recv_message['opcode'] == OPCODE['Other wallets']:
                    print(f'Client {client_address} want to get other wallets')
                    answer = get_other_wallets(client_address)
                elif recv_message['opcode'] == OPCODE['Transaction']:
                    print(f'Client {client_address} wants to make a transaction to the '
                          f'{recv_message["wallet_num"]} for the amount {recv_message["sum"]}')
                    answer = transaction(client_address, recv_message['wallet_num'], recv_message['sum'])
                elif recv_message['opcode'] == OPCODE['Sum']:
                    print(f'Client {client_address} wants to check the status of the wallet')
                    answer = get_sum(client_address)
                request = {'opcode': OPCODE['Answer'], 'answer': answer}
                print(f'Sending to client {client_address} a response - {answer}')
                json_request = json.dumps(request).encode(CODE)
                request_header = f"{len(json_request):<{BLOCK_LENGTH}}".encode(CODE)
                sock.send(request_header + json_request)
            else:
                print(f'Closed connection from: {client_address}')
                try:
                    del users[client_address]
                except KeyError:
                    pass
                client_sockets.remove(sock)
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                return
        except ConnectionResetError:
            print(f'Closed connection from: {client_address}')
            try:
                del users[client_address]
            except KeyError:
                pass
            client_sockets.remove(sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print(f'Listening for connections on {IP}:{PORT}...')
    try:
        while True:
            client_socket, client_address = client_connect(server_socket)
            threading.Thread(target=recv_request, args=(client_socket, client_address)).start()
    except:
        for sock in client_sockets:
            sock.close()
        server_socket.close()
        print('Server is closed')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Server is closed')
