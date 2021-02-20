import socket
from threading import Thread
import sys
import tftp_utils as tftputils
import server_utils as utils
from queue import Queue

ip = "127.0.0.1"
port = 5005

ack_queue = Queue()
data_queue = Queue()

tftp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tftp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tftp_socket.bind((ip, port))

# подключенные пользователи, их обработка уже начата
users = dict()


# поток на отправку
def handle_request(request, address):
    print('Sending thread started')
    print(request, sep='\n')
    users[address[0]] = request
    if request['OPCODE'] == tftputils.TFTPOpcodes['RRQ']:
        res = utils.sending_file_from_server(tftp_socket, address, request, ack_queue)
        msg = 'File sent successfully'
    elif request['OPCODE'] == tftputils.TFTPOpcodes['WRQ']:
        res = utils.receiving_file_from_client(tftp_socket, addr, 'server', data_queue, request)
        msg = 'File received successfully'
    else:
        # ILLEGAL OPCODE ERROR
        tftputils.Socket.sendto(tftp_socket, addr, tftputils.ERROR.send(4))
        res = True
        msg = 'ILLEGAL OPCODE ERROR OCCURRED'
    if res:
        del users[address[0]]
        print(msg)


# поток на прием сообщений, постоянное прослушивание
while True:
    try:
        data, addr = tftputils.Socket.recv(tftp_socket)
        handled_msg = tftputils.process_data(data)
        # check if this connection is already in handling
        if addr[0] in users.keys():
            if handled_msg['OPCODE'] == tftputils.TFTPOpcodes['ACK']:
                ack_queue.put((addr, handled_msg['BLOCK_NUM']))
                print('ACK package received, added to queue')
            elif handled_msg['OPCODE'] == tftputils.TFTPOpcodes['DATA']:
                data_queue.put((addr, handled_msg['BLOCK_NUM'], handled_msg['DATA']))
                print('Data package received, added to queue')
        else:
            Thread(target=handle_request, args=(handled_msg, addr), daemon=True).start()
    except KeyboardInterrupt:
        tftp_socket.close()
        print('Server is stopped')
        sys.exit(0)
