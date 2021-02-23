import tftp_utils as utils
import time
import logging.config

SERVER_TIMEOUT = 10

logging.config.fileConfig('server_logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


# обрабатывает процесс чтения файла с сервера (отправка с сервера)
def sending_file_from_server(sock, addr, request, ack_queue, timeout=SERVER_TIMEOUT):
    send_timeout = timeout
    try:
        send_file = open('server/' + request['FILENAME'], 'rb')
        send_data = send_file.read(utils.BLOCK_SIZE)
        block_num = 1
        utils.Socket.sendto(sock, addr, utils.DATA.send(send_data, block_num))
        while send_file:
            if ack_queue.empty() is False and send_timeout != 0:
                recent_ack = ack_queue.get()
                if (recent_ack[0] == addr) and (recent_ack[1] == block_num):
                    send_data = send_file.read(utils.BLOCK_SIZE)
                    if len(send_data) == 0:
                        break
                    block_num += 1
                    utils.Socket.sendto(sock, addr, utils.DATA.send(send_data, block_num))
                else:
                    ack_queue.put(recent_ack)
                    time.sleep(1)
                    send_timeout -= 1
            elif send_timeout == 0:
                utils.Socket.sendto(sock, addr, utils.ERROR.send(0, 'Message: timeout reached'))
                logger.info('Message: timeout reached')
        send_file.close()
        return True

    except FileNotFoundError:
        utils.Socket.sendto(sock, addr, utils.ERROR.send(1))
        logger.error(FileNotFoundError)
        return False


# обрабатывает процесс записи файла на сервера (прием на сервере)
def receiving_file_from_client(sock, addr, type_op, data_queue, request, timeout=SERVER_TIMEOUT):
    utils.Socket.sendto(sock, addr, utils.ACK.send(0))
    recent_data = data_queue.get()
    block_num = 1
    rec_timeout = timeout
    file_data = None
    while rec_timeout != 0:
        if (addr == recent_data[0]) and (block_num == recent_data[1]):
            recv_data, received_block_num = recent_data[2], recent_data[1]
            file_data = recv_data
            while len(recv_data) == utils.BLOCK_SIZE:
                if block_num == received_block_num:
                    utils.Socket.sendto(sock, addr, utils.ACK.send(block_num))
                    block_num += 1
                    recent_data = data_queue.get()
                    recv_data, received_block_num = recent_data[2], recent_data[1]
                    file_data += recv_data
                else:
                    file_data = file_data[:512 * (received_block_num - 1)]
                    utils.Socket.sendto(sock, addr, utils.ACK.send(block_num))
                    block_num = received_block_num + 1
                    recent_data = data_queue.get()
                    recv_data, received_block_num = recent_data[2], recent_data[1]
                    file_data += recv_data
            utils.Socket.sendto(sock, addr, utils.ACK.send(block_num))
            block_num += 1
            rec_timeout = 0
            # print('File was received fully')
            logger.info('File was received fully')
        else:
            data_queue.put(recent_data)
            time.sleep(1)
            rec_timeout -= 1
    sock.sendto(utils.ACK.send(block_num), addr)
    file = open(type_op + '/' + request['FILENAME'], 'wb')
    file.write(file_data)
    logger.info('File was saved')
    print('File was saved')
    file.close()
    return True
