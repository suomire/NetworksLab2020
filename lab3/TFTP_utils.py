import socket
import logging
from enum import Enum
import struct

logger = logging.getLogger('tftpd')

BLOCK_SIZE = 512
BUFFER_SIZE = 65536
TIMEOUT = 100

ip = "127.0.0.1"
port = 7556
tftp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tftp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tftp_socket.bind((ip, port))  # localhost, port
logging.info('TFTP Server started, listening on %s', (ip, port))

TFTPOpcodes = {'RRQ': 1,
               'WRQ': 2,
               'DATA': 3,
               'ACK': 4,
               'ERROR': 5}


class TFTPOpcodesClass(Enum):
    RRQ = 1
    WRQ = 2
    DATA = 3
    ACK = 4
    ERROR = 5


MODES = ['netascii', 'octet', 'mail']

ErrorCodeMsg = {0: 'Not defined, see error message (if any)',
                1: 'File not found',
                2: 'Access violation',
                3: 'Disk full or allocation exceeded',
                4: 'Illegal TFTP operation',
                5: 'Unknown transfer ID',
                6: 'File already exists',
                7: 'No such user'}


class UserRequest:

    def __init__(self, opcode, mode, filename):
        self.request_opcode = opcode
        self.mode = mode
        self.filename = filename
        self.current_block_number = 1
        self.ack_for_current_block = False

    def remove(self):
        self.request_opcode = None
        self.mode = None
        self.filename = None
        self.current_block_number = None
        self.ack_for_current_block = None
        pass


class RRQ:

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode


class WRQ:

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.ack = 0


class DATA:
    block_num = 0
    data = None

    def __init__(self, data):
        """
        Create protocol package from received request
        :param req: dict which contains all request properties
        """
        self.block_num += 1
        self.data = data
        self.opcode = TFTPOpcodes['DATA']

    @staticmethod
    def send(data):
        return DATA(data)


class ACK:
    # ack for WRQ started with number = 0

    def __init__(self, block_num):
        self.block_num = block_num

    @staticmethod
    def send(req):
        # TODO: check errors for this kind of action (?)
        return ACK(req)


class ERROR:

    def __init__(self, err_code, err_msg):
        self.err_code = err_code
        self.err_msg = err_msg


class Server:

    @staticmethod
    def recv(sock):
        # TODO: CHECK FOR ILLEGAL OPCODE ERROR
        data, addr = sock.recvfrom(BUFFER_SIZE)
        print(f'Received packet from {addr}')
        return data, addr

    @staticmethod
    def sendto(sock, addr, msg):
        send_msg = struct.pack('!h', msg.opcode) + struct.pack('!h', msg.block_num) + msg.data
        sock.sendto(send_msg, addr)
        print(f'Sending packet to {addr}')


def process_data(msg):
    request = dict()
    request['OPCODE'] = struct.unpack('!h', msg[:2])[0]
    if request['OPCODE'] == TFTPOpcodes['RRQ'] or request['OPCODE'] == TFTPOpcodes['WRQ']:
        request['FILENAME'] = msg[2:].split(b'\0')[0].decode('utf-8')
        request['MODE'] = msg[2:].split(b'\0')[1].decode('utf-8')
    elif request['OPCODE'] == TFTPOpcodes['DATA']:
        request['BLOCK_NUM'] = msg[2:].split(b'\0')[0].decode('utf-8')
        request['DATA'] = msg[2:].split(b'\0')[1].decode('utf-8')
    elif request['OPCODE'] == TFTPOpcodes['ACK']:
        request['BLOCK_NUM'] = msg[2:].split(b'\0')[0].decode('utf-8')
    else:
        request['ERRCODE'] = msg[2:].split(b'\0')[0].decode('utf-8')
        request['ERRMSG'] = msg[2:].split(b'\0')[1].decode('utf-8')
    return request


def recv():
    data, address = tftp_socket.recvfrom(BUFFER_SIZE)
    process_data(data)
