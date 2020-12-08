import socket
import struct
import TFTP_utils as Utils

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MESSAGE = b'HELLO WORLD WITH UDP'
ADDRESS = (UDP_IP, UDP_PORT)
print(ADDRESS)

tftp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# tftp_client_socket.sendto(MESSAGE, ADDRESS)

filename = 'file.jpg'.encode('utf-8')
opcode = Utils.TFTPOpcodes['RRQ']
opcode_filename = struct.pack('!h', opcode) + filename
mode = 'netascii'.encode('utf-8')
msg = b'\0'.join([opcode_filename, mode])

tftp_client_socket.sendto(msg, ADDRESS)

print(msg)

print(msg[2:].split(b'\0'), sep='\n')
print(struct.unpack('!h', msg[:2])[0])
print(Utils.process_data(msg))

data = tftp_client_socket.recv(Utils.BUFFER_SIZE)
file = open('received_file.txt', 'wb')
file.write(data[4:])
print(data[4:])
