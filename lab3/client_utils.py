import tftp_utils as utils
import argparse
import socket
import logging.config

ERR_MAX = 5

logging.config.fileConfig('client_logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='TFTP client.')
    parser.add_argument('host', help='hostname/IP of TFTP-server', nargs='?')
    parser.add_argument('port', help='port of TFTP-server', default=69, nargs='?', type=int)
    exclusive_operations = parser.add_mutually_exclusive_group(required=True)
    exclusive_operations.add_argument('-g', '--get', metavar='FILENAME', help='Name of the file to download')
    exclusive_operations.add_argument('-p', '--put', metavar='FILENAME', help='Name of the file to upload')
    parser.add_argument('-f', '--filename', metavar='FILENAME',
                        help='Filename/filepath for session. Same as in the get/put command by default')
    parser.add_argument('timeout', help='Timeout for client and server', default=10, nargs='?', type=int)
    return parser


def handle_message(data):
    recv_data = utils.process_data(data)
    recv_block_num = recv_data['BLOCK_NUM']
    recv_file_data = recv_data['DATA']
    return recv_block_num, recv_file_data,


# put
def sending_file_from_client(timeout, addr, msg, request):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    utils.Socket.sendto(sock, addr, msg)
    block_num = 0
    err = 0
    send_file = open('client/' + request['FILENAME'], 'rb')
    send_data = send_file.read(utils.BLOCK_SIZE)
    last_send = send_data

    while True:
        sock.settimeout(timeout)
        try:
            recent_ack, addr = utils.Socket.recv(sock)

        except socket.timeout:
            if block_num == 0:
                print("Server is not responding.")
                return
            if err < ERR_MAX:
                err += 1
                utils.Socket.sendto(sock, addr, last_send)
                continue
            else:
                logger.error('Server is not responding')
                # print("Server is not responding")
                return

        recent_ack = utils.process_data(recent_ack)

        if recent_ack['OPCODE'] == utils.TFTPOpcodes['ERROR']:
            print(f"Error from server: {recent_ack['ERRMSG']}")
            logger.error(f"Error from server: {recent_ack['ERRMSG']}")
            send_file.close()
            # sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            break

        elif recent_ack['OPCODE'] == utils.TFTPOpcodes['ACK']:
            block_num += 1
            last_message = utils.DATA.send(send_data, block_num)
            utils.Socket.sendto(sock, addr, last_message)
            if len(send_data) < utils.BLOCK_SIZE:
                print('File was sent')
                logger.info('File was sent')
                send_file.close()
                # sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                break
            else:
                send_data = send_file.read(utils.BLOCK_SIZE)


# get
def receiving_file(timeout, addr, type_op, request, filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    utils.Socket.sendto(sock, addr, request)
    block_num = 1
    data, addr = utils.Socket.recv(sock)
    print(data)
    received_block_num, recv_data = handle_message(data)
    print('received block num: ', received_block_num)
    file_data = recv_data
    while len(recv_data) == utils.BLOCK_SIZE:
        print('512 block received')
        if block_num == received_block_num:
            sock.sendto(utils.ACK.send(block_num), addr)
            block_num += 1
            data, _ = utils.Socket.recv(sock)
            print(data)
            received_block_num, recv_data = handle_message(data)
            file_data += recv_data
        else:
            file_data = file_data[:512 * (received_block_num - 1)]
            sock.sendto(utils.ACK.send(block_num - 1), addr)
            block_num = received_block_num
            data, _ = utils.Socket.recv(sock)
            received_block_num, recv_data = handle_message(data)
            file_data += recv_data
        print('received block num: ', received_block_num)
    sock.sendto(utils.ACK.send(block_num), addr)
    file = open(type_op + filename, 'wb')
    file.write(file_data)
    file.close()
    print('File received successfully')
