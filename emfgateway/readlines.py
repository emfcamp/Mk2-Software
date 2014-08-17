import select

def readlines(sock, recv_buffer=4096, delim='\n', timeout_in_seconds=30.0):
    buffer = ''
    data = True
    while data:
        readable, writable, exceptional = select.select([sock], [], [], timeout_in_seconds)

        if not readable:
            raise Exception("TCP read timeout reached or connection closed")

        data = sock.recv(recv_buffer)
        buffer += data

        if len(data) == 0:
            raise Exception("No data received - connection has probably been closed")

        while buffer.find(delim) != -1:
            line, buffer = buffer.split('\n', 1)
            yield line
    return