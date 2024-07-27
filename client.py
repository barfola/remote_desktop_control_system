# THE CLIENT SIDE WILL RUN ON THE CONTROLLED PC
import socket
from io import BytesIO
from PIL import ImageGrab


def send_data(socket_connection: socket.socket, data, is_text=False):
    """
    This function sends data threw socket connection according protocol.
    According to the protocol first 4 bytes represents the data size.

    :param socket_connection:
    :param data:
    :return None:
    """

    data_length_in_binary = (1+len(data)).to_bytes(4, byteorder='big')

    if isinstance(data, str):
        data = data.encode()

    if is_text:
        data = b't' + data
    else:
        data = b'b' + data

    try:
        socket_connection.sendall(data_length_in_binary)
        socket_connection.sendall(data)
    except ConnectionAbortedError:
        print('> Connection error during data delivering.')

    except Exception as error:
        print(f'> Connection error during data delivering.{error}.')


def receive_data(socket_connection: socket.socket):
    """
    This function receive data according protocol.
    :param socket_connection:
    :return decode_data:
    :rtype str or None:
    """
    data_length_in_decimal = int.from_bytes(socket_connection.recv(4), byteorder='big')
    data = b''

    while len(data) < data_length_in_decimal:
        try:
            data_chunk = socket_connection.recv(min(1024, data_length_in_decimal - len(data)))
            data += data_chunk

        except RuntimeError:
            print('> Data is not sent fully, connection closed before full message was sent.')
            return None

        except Exception as error:
            print(f'> Error occurred when receiving data. {error}.')
            return None

    if data[0:1] == b't':
        data = data[1:].decode()
    else:
        data = data[1:]
    return data


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot


def send_screen_shot(socket_connection: socket.socket):
    try:
        while True:
            screenshot = get_screenshot()
            image_buffer = BytesIO()
            screenshot.save(image_buffer, format='PNG')
            image_data = image_buffer.getvalue()
            send_data(socket_connection, image_data, is_text=False)
    finally:
        socket_connection.close()


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('10.100.102.16', 50000))

send_screen_shot(client_socket)