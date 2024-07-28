# THE CLIENT SIDE WILL RUN ON THE CONTROLLED PC
import socket
from io import BytesIO
from PIL import ImageGrab
import pyautogui
import pickle
from helper import get_screen_size
import threading


def send_data(socket_connection: socket.socket, data, is_text=False):
    """
    This function sends data threw socket connection according protocol.
    According to the protocol first 4 bytes represents the data size.

    :param socket_connection:
    :param data:
    :return None:
    """

    data_length_in_binary = (1 + len(data)).to_bytes(4, byteorder='big')

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
        print(f'> Connection error during data delivering.{error}')


def receive_data(socket_connection: socket.socket):
    """
    This function receive data according protocol.
    :param socket_connection:
    :return decode_data:
    :rtype str:
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
            print(f'> Error occurred when receiving data.{error}')
            return None

    if data[0:1] == b't':
        data = data[1:].decode()
    else:
        data = data[1:]
    return data


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot


def send_screen_shot(client_socket: socket.socket):
    try:
        while True:
            screenshot = get_screenshot()
            img_buffer = BytesIO()
            screenshot.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            send_data(client_socket, img_data, is_text=False)
    finally:
        client_socket.close()


def receive_server_mouse_coordinates(socket_connection: socket.socket):
    pyautogui.FAILSAFE = False
    server_screen_size = receive_data(socket_connection)
    server_screen_width, server_screen_height = pickle.loads(server_screen_size)
    client_screen_width, client_screen_height = get_screen_size()
    screens_width_ratio = client_screen_width / server_screen_width
    screens_height_ratio = client_screen_height / server_screen_height
    try:
        while True:
            server_mouse_coordinates = receive_data(socket_connection)
            server_x_coordinate, server_y_coordinate = pickle.loads(server_mouse_coordinates)
            print(f'server coordinates {server_x_coordinate},{server_y_coordinate}')
            client_x_coordinate = int(server_x_coordinate * screens_width_ratio)
            client_y_coordinate = int(server_y_coordinate * screens_height_ratio)
            print(f'The coordinates are {client_x_coordinate},{client_y_coordinate}')
            pyautogui.moveTo(client_x_coordinate, client_y_coordinate)
    except KeyboardInterrupt:
        print(f'{KeyboardInterrupt} while receiving coordinates.')
    except Exception as error:
        print(f'{error} while receiving coordinates.')


my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
my_socket.connect(('10.100.102.16', 50000))
#send_screen_shot(my_socket)
screen_thread = threading.Thread(target=send_screen_shot, args=(my_socket,))
#receive_server_mouse_coordinates(socket_connection=my_socket)
mouse_thread = threading.Thread(target=receive_server_mouse_coordinates, args=(my_socket,))
screen_thread.start()
mouse_thread.start()

screen_thread.join()
mouse_thread.join()