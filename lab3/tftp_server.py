import socket
import logging
from threading import Thread
import sys
import TFTP_utils as Utils
from TFTP_utils import Server

ip = "127.0.0.1"
port = 5005

BUFFER_SIZE = 65536

tftp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tftp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tftp_socket.bind((ip, port))  # localhost, port

logging.info('TFTP Server started, listening on', (ip, port))

users = dict()


def handle_request(msg, address):
    print('Thread started')
    print(msg, sep='\n')
    request = Utils.process_data(msg)
    if address not in users.keys():
        users[address] = Utils.UserRequest(request['OPCODE'], request['MODE'], request['FILENAME'])

    if request['OPCODE'] == Utils.TFTPOpcodes['RRQ']:
        # SEND DATA (packets)
        send_file = open(request['FILENAME'], 'rb')
        send_data = send_file.read(Utils.BLOCK_SIZE)
        while send_file:
            Server.sendto(tftp_socket, address, Utils.DATA.send(send_data))
            # TODO: wait timeout for ACK ??
            # create timeout mechanism and with trigger variable
            while users[address].ack_for_current_block is not True:
                # wait
                pass

    elif request['OPCODE'] == Utils.TFTPOpcodes['WRQ']:
        # SEND ACK AND THEN RECEIVE DATA
        Server.sendto(tftp_socket, address, Utils.ACK.send(request))
        pass
    elif request['OPCODE'] == Utils.TFTPOpcodes['DATA']:
        # SEND ACK
        pass
    elif request['OPCODE'] == Utils.TFTPOpcodes['ACK']:
        # ALLOWS TO CONTINUE SENDING DATA
        pass
    elif request['OPCODE'] == Utils.TFTPOpcodes['ERROR']:
        # SOME ERROR OCCURRED ??
        pass
    else:
        # ILLEGAL OPCODE
        pass


while True:
    try:
        # receive data, write own method to process data to structure
        data, addr = Server.recv(tftp_socket)
        print(data, addr)
        Thread(target=handle_request, args=(data, addr)).start()
    except KeyboardInterrupt:
        print('Server is stopped')
        sys.exit(0)

# TODO: очистка словоря с пользователями (например, после выполнения потока обработки. метод remove вызывается если
#  происходит действие, которое точно обозначает корректное завершение передачи )
