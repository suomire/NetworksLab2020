import socket
import json
import sys

try:
    IP = sys.argv[1]
except IndexError:
    IP = 'localhost'
try:
    PORT = int(sys.argv[2])
except IndexError:
    PORT = 5454

CODE = 'utf-8'
BLOCK_LENGTH = 512
USERNAME = None
PASSWORD = None

OPCODE = {
    'Register': 0,
    'Sign in': 1,
    'Other wallets': 2,
    'Transaction': 3,
    'Sum': 4,
    'Answer': 5
}

COMMANDS = {
    0: "User registration",
    1: "Log in ",
    2: "Request all user's wallets",
    3: "Make a transaction to user",
    4: "Check your account status",
    -1: "Help",
    111: "Close client"
}


def process_recv_message(sock, recv_message, request):
    print(recv_message)
    global USERNAME, PASSWORD
    if recv_message['opcode'] == OPCODE['Answer']:
        if request['opcode'] == OPCODE['Register']:  # User registration
            print('Congratulations! Your registration was successful')
            print('Your account information:')
            print('Username: %s \n Wallet number: %s' % (request['name'], recv_message['answer']))
        elif request['opcode'] == OPCODE['Sign in']:  # Log in
            if recv_message['answer'] is False:
                print('Something was wrong. Check your username/password and try again')
                USERNAME, PASSWORD = None, None
            else:
                print('Congratulations! You are logged in successfully')
                print('Your account information:')
                print('Username: %s \n Wallet number: %s' % (request['name'], recv_message['answer']))
        elif request['opcode'] == OPCODE['Other wallets']:  # Request all user's wallets
            print('The list of other wallets in system')
            # list of lists
            print("Username \t\t Wallet number")
            for pair in recv_message['answer']:
                print(pair[0], ' \t\t', pair[1])
        elif request['opcode'] == OPCODE['Sum']:  # Check your account status
            print('Your account information:')
            print('Total: %d' % (recv_message['answer']))
        elif request['opcode'] == OPCODE['Transaction']:
            if recv_message['answer'] is False:
                print('You do not have enough funds in your account')
            else:
                print('Congratulations! You have got a successful transaction')
                request = {'opcode': OPCODE['Sum']}
                process_recv_message(sock, send_req_n_get_answer(sock, request), request)
    return


def send_req_n_get_answer(sock, request):
    json_request = json.dumps(request).encode(CODE)
    sock.send(json_request)
    recv_message = sock.recv(BLOCK_LENGTH)
    if recv_message:
        recv_message = json.loads(recv_message)
        return recv_message
    else:
        print('Server is closed')
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        print("Connection closed by the server")
        sys.exit(0)


def login_usr_pass():
    print('Enter username:')
    username = input()
    print('Enter password')
    password = input()
    return username, password


def working_session(sock):
    global USERNAME, PASSWORD
    print("Welcome to our very primitive paying system!")
    print("Enter '-1' to get a list of available actions")
    while True:
        try:
            command = int(input())
            if (USERNAME is None) and (command not in [0, 1]):
                print('You are not logged in')
                print("Enter command '0' to register new user or '1' to log in")
            elif (command == OPCODE['Register']) or (command == OPCODE['Sign in']):  # User registration
                USERNAME, PASSWORD = login_usr_pass()
                request = {'opcode': command, 'name': USERNAME, 'password': PASSWORD}
                print(request)
                recv_message = send_req_n_get_answer(sock, request)
                process_recv_message(sock, recv_message, request)
            elif (command == OPCODE['Other wallets']) or (command == OPCODE['Sum']):  # Request all user's wallets
                request = {'opcode': command}
                recv_message = send_req_n_get_answer(sock, request)
                process_recv_message(sock, recv_message, request)
            elif command == OPCODE['Transaction']:  # Make a transaction to user
                print('Enter the wallet number you want to send money to')
                wallet_number = input()
                print('How much do you want to transfer?')
                summary = float(input())
                request = {'opcode': command, "wallet_num": wallet_number, "sum": summary}
                recv_message = send_req_n_get_answer(sock, request)
                process_recv_message(sock, recv_message, request)
            elif command == -1:
                for elem in COMMANDS:
                    print(elem.key, ' -- ', elem.value)

            elif command == 111:
                print('Closing client application...')
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                print('Client application is closed.')
                print('Goodbye!')
                sys.exit(0)
            else:
                print('Unknown command. Please, try again or enter <<help>>')
        except ValueError:
            print('Please, enter a number.')


def main():
    print("Pay system client started.")
    try:
        address = (IP, PORT)
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect(address)
    except ConnectionRefusedError:
        print('Server is closed')
        return
    working_session(client_sock)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Client is closed')
