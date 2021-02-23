import struct
import logging.config

logging.config.fileConfig('server_logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

BLOCK_SIZE = 512
BUFFER_SIZE = 65536

TFTPOpcodes = {'RRQ': 1,
               'WRQ': 2,
               'DATA': 3,
               'ACK': 4,
               'ERROR': 5}

ErrorCodeMsg = {0: 'Not defined, see error message (if any)',
                1: 'File not found',
                2: 'Access violation',
                3: 'Disk full or allocation exceeded',
                4: 'Illegal TFTP operation',
                5: 'Unknown transfer ID',
                6: 'File already exists',
                7: 'No such user'}


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
    data = None

    def __init__(self, data, block_num):
        self.block_num = block_num
        self.data = data
        self.opcode = TFTPOpcodes['DATA']

    @staticmethod
    def send(data, block_num):
        send_data = DATA(data, block_num)
        send_message = struct.pack(b'!2H', send_data.opcode, send_data.block_num) + send_data.data
        return send_message


class ACK:
    # ack for WRQ started with number = 0

    def __init__(self, block_num):
        self.block_num = block_num
        self.opcode = TFTPOpcodes['ACK']
        self.data = None

    @staticmethod
    def send(block_num):
        ack = ACK(block_num)
        # send_message = struct.pack('!h', ack.opcode) + struct.pack('!h', ack.block_num)
        send_message = struct.pack(b'!2H', ack.opcode, ack.block_num)
        logger.info('Sending ACK ' + block_num)
        return send_message


class ERROR:

    def __init__(self, err_code, err_msg):
        self.err_code = err_code
        self.err_msg = err_msg
        self.opcode = 5

    @staticmethod
    def send(err_code, msg=' '):
        error = ERROR(err_code, ErrorCodeMsg[err_code])
        errmsg = error.err_msg + msg
        send_message = struct.pack('!h', error.opcode) + struct.pack('!h', error.err_code) + errmsg.encode(
            'utf-8')
        logger.error('Sending ERROR ' + err_code + ': ' + error.err_msg)
        return send_message


class Socket:

    @staticmethod
    def recv(sock):
        data, addr = sock.recvfrom(BUFFER_SIZE)
        logger.info(f'Received packet from {addr}')
        return data, addr

    @staticmethod
    def sendto(sock, addr, msg):
        sock.sendto(msg, addr)
        logger.info(f'Sending packet to {addr}')


def process_data(msg):
    request = dict()
    request['OPCODE'] = struct.unpack('!h', msg[:2])[0]
    if request['OPCODE'] == TFTPOpcodes['RRQ'] or request['OPCODE'] == TFTPOpcodes['WRQ']:
        request['FILENAME'] = msg[2:].split(b'\0')[0].decode('utf-8')
        request['MODE'] = msg[2:].split(b'\0')[1].decode('utf-8')
    elif request['OPCODE'] == TFTPOpcodes['DATA']:
        request['BLOCK_NUM'] = struct.unpack('!h', msg[2:4])[0]
        request['DATA'] = msg[4:]
    elif request['OPCODE'] == TFTPOpcodes['ACK']:
        request['BLOCK_NUM'] = struct.unpack('!h', msg[2:])[0]
    else:
        request['ERRCODE'] = struct.unpack('!h', msg[2:4])[0]
        request['ERRMSG'] = msg[4:-1].decode('utf-8')  # last symbol is not included ('\0')
    return request
