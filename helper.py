import socket
import pyautogui


def send_data(socket_connection: socket.socket, data, is_text=False):
    """
    This function sends data threw socket connection according protocol.
    According to the protocol first 4 bytes represents the data size.

    :param socket_connection:
    :param data:
    :param is_text
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
        print(f'> Connection error during data delivering.{ConnectionAbortedError}.')

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


def get_screen_size():
    return pyautogui.size()


def is_mouse_change_coordinates(current_x_coordinate, current_y_coordinate, prior_x_coordinate, prior_y_coordinate):
    if current_x_coordinate != prior_x_coordinate:
        return True

    if current_y_coordinate != prior_y_coordinate:
        return True

    return False


def close_socket_connections(socket_connections_list):
    for socket_connection in socket_connections_list:
        print(socket_connection)
        socket_connection.close()


if __name__ == '__main__':
    ...
