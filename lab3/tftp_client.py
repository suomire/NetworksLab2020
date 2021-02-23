import struct
import tftp_utils as tftputils
import client_utils as utils
import os
import logging.config

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
address = None
tftp_client_socket = None

MODE = 'octet'

logging.config.fileConfig('client_logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def create_request(opcode, filename, mode='octet'):
    logger.info(msg='Request created')
    filename = filename.encode('utf-8')
    opcode_filename = struct.pack('!h', opcode) + filename
    mode = mode.encode('utf-8')
    msg = b'\0'.join([opcode_filename, mode]) + b'\0'
    return msg


def main():
    global address
    parser = utils.create_parser()
    args = parser.parse_args()

    address = (args.host, args.port)
    print(address)

    if args.get:
        msg = create_request(tftputils.TFTPOpcodes['RRQ'], args.get)
        print(msg)
        utils.receiving_file(args.timeout, address, 'client/', msg, args.get)
    elif args.put:
        if os.path.isfile('client/' + args.put):
            msg = create_request(tftputils.TFTPOpcodes['WRQ'], args.put)
            print(msg)
            utils.sending_file_from_client(args.timeout, address, msg, tftputils.process_data(msg))
        else:
            logger.error('File does not exist.')
    else:
        logger.error(msg='Command error occurred. Please, try again')


if __name__ == '__main__':
    main()
