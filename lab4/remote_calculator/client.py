import re
import socket
import json

"""
Written by Koknov Nikolay, 70202
"""

# IP = "localhost"
IP = '51.15.130.137'
PORT = 5454
CODE = 'utf-8'
BLOCK_LENGTH = 128
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
    if recv_request['opcode'] == OPCODE['answer']:
        answer = recv_request['num']
        return answer
    else:
        return False


def send_recv_request(sock, request):
    while True:
        try:
            json_request = json.dumps(request).encode(CODE)
            sock.send(json_request)
            recv_message = sock.recv(BLOCK_LENGTH).decode(CODE)
            if recv_message:
                recv_message = json.loads(recv_message)
                answer = get_answer(recv_message)
                return answer
            else:
                print('Server closed')
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                exit(0)
        except ConnectionResetError:
            print('Server closed')
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            exit(0)


def main():
    print("Calculator client started.")
    try:
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((IP, PORT))
    except ConnectionRefusedError:
        print('Server closed')
        return
    while True:
        print("Enter \"1\" - for quick operation(+,-,*,/);\n"
              "Enter \"2\" - for long operation(arg!, sqrt(arg))\n"
              "Enter \"!exit\" - for exit from calculator")
        input_operation = input().replace(" ", "")
        if input_operation:
            if input_operation == '1' or input_operation == "2" or input_operation == "!exit":
                if input_operation == "!exit":
                    print("Goodbye!")
                    return
                elif input_operation == "1":
                    while True:
                        input_message = input("Enter: arg1 +|-|*|/ arg2\n"
                                              "Enter \"!back\" - for back to choose operation.\n")
                        if input_message:
                            if input_message == "!exit":
                                print("Goodbye!")
                                return
                            elif input_message == "!back":
                                break
                            for_check = input_message.replace(" ", "")
                            match_1 = re.match(r"-?(\d+\.)?\d+[+\-*/]-?(\d+\.)?\d+", for_check)
                            if match_1 and len(match_1.group()) == len(for_check):
                                if re.match(r"(\d+\.)?\d+-(\d+\.)?\d+", for_check):
                                    example = for_check.replace('-', ' - ')
                                elif re.match(r"-(\d+\.)?\d+-(\d+\.)?\d+", for_check):
                                    example = '-' + for_check.split('-')[1] + ' - ' + for_check.split('-')[2]
                                elif re.match(r"(\d+\.)?\d+--(\d+\.)?\d+", for_check):
                                    example = for_check.split('-')[0] + ' - ' + '-' + for_check.split('-')[2]
                                elif re.match(r"-(\d+\.)?\d+--(\d+\.)?\d+", for_check):
                                    example = '-' + for_check.split('-')[1] + ' - ' + '-' + for_check.split('-')[3]
                                else:
                                    example = input_message.replace(" ", "").replace('+', ' + ') \
                                        .replace('*', ' * ').replace('/', ' / ')
                            else:
                                print('Your command is wrong')
                                continue
                            ex_arguments = example.split(" ")
                            try:
                                arg1 = float(ex_arguments[0])
                                arg2 = float(ex_arguments[2])
                            except ValueError:
                                print('Arg must be number')
                                continue
                            op = ex_arguments[1]
                            if op not in OPCODE:
                                print('Operation must be +|-|*|/')
                                continue
                            if OPCODE[op] == 3 and arg2 == 0:
                                print('Сan`t be divided by 0')
                                continue
                            request = {'opcode': OPCODE[op], 'num1': arg1, 'num2': arg2}
                            answer = send_recv_request(client_sock, request)
                            print(f'{arg1} {op} {arg2} = {answer}')
                elif input_operation == "2":
                    while True:
                        input_message = input("Enter: arg! or sqrt(arg)\n"
                                              "Enter \"!back\" - for back to choose operation.\n").replace(' ', '')
                        if input_message:
                            if input_message == "!exit":
                                print("Goodbye!")
                                return
                            elif input_message == "!back":
                                break
                            elif input_message[-1] == '!':
                                try:
                                    arg = int(input_message[:-1])
                                except ValueError:
                                    print('Arg must be integer')
                                    continue
                                op = input_message[-1]
                            elif input_message[-1] == ')':
                                try:
                                    arg = float(input_message[5:-1])
                                except ValueError:
                                    print('Arg must be number')
                                    continue
                                op = input_message[:4]
                            else:
                                print('Your command is wrong\n')
                                continue
                            if arg < 0:
                                print('Arg must be positive')
                                continue
                            request = {'opcode': OPCODE[op], 'num': arg}
                            answer = send_recv_request(client_sock, request)
                            if op == '!':
                                print(f'{arg}! = {answer}')
                            else:
                                print(f'sqrt({arg}) = {answer}')
            else:
                print('Your command is wrong')
                continue


if __name__ == '__main__':
    main()
