def encode_message(message):
    timeline = message[0].encode('utf-8')
    username = message[1].encode('utf-8')
    msg_content = message[2].encode('utf-8')
    msg = b'\0'.join([timeline, username, msg_content])
    return msg


def message_processing(message):
    msg = [m.decode('utf-8') for m in message.split(b'\0')]
    return msg
