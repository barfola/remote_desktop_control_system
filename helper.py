import socket
import pyautogui
from pynput.mouse import Listener, Controller
from pynput import keyboard
import pickle
import time
import keyboard

#receive_data, send_data, get_screen_size, is_mouse_change_coordinates, close_socket_connections

def send_keyboard_clicks(socket_connection: socket.socket):
    while True:
        keyboard_click_event = keyboard.read_event()
        keyboard_click_event_in_binary = pickle.dumps(keyboard_click_event)
        send_data(socket_connection, keyboard_click_event_in_binary)


def click_keyboard_button(keyboard_click_event):
    keyboard_key = keyboard_click_event.event_name
    keyboard.press(keyboard_key)


def release_keyboard_button(keyboard_click_event):
    keyboard_key = keyboard_click_event.event_name
    keyboard.release(keyboard_key)


def receive_keyboard_clicks(socket_connection: socket.socket):
    while True:
        keyboard_click_event_in_binary = receive_data(socket_connection)
        keyboard_click_event = pickle.loads(keyboard_click_event_in_binary)
        if keyboard_click_event.event_type == 'down':
            print('down')


def send_mouse_scrolls_data(socket_connection: socket.socket):

    def on_scroll(x_coordinate, y_coordinate, x_difference, y_difference):
        mouse_scroll_data_tuple = (x_difference, y_difference)
        mouse_scroll_data_tuple_in_binary = pickle.dumps(mouse_scroll_data_tuple)
        send_data(socket_connection, mouse_scroll_data_tuple_in_binary)

        print(mouse_scroll_data_tuple)

    with Listener(on_scroll=on_scroll) as listener:
        listener.join()


def mouse_scrolling(socket_connection: socket.socket):
    while True:
        mouse_scroll_data_tuple_in_binary = receive_data(socket_connection)
        mouse_scroll_data_tuple = pickle.loads(mouse_scroll_data_tuple_in_binary)
        x_difference = mouse_scroll_data_tuple[0]
        y_difference = mouse_scroll_data_tuple[1]
        print(f'{x_difference},{y_difference}')


def send_mouse_click_data(socket_connection: socket.socket):
    def on_click(x_coordinate, y_coordinate, button, pressed):
        if pressed:
            click_data = {'x_coordinate': x_coordinate,
                          'y_coordinate': y_coordinate,
                          'button': str(button)}
            print(f'x : {x_coordinate}')
            print(f'y : {y_coordinate}')
            print(f'button : {button}')
            mouse_click_binary_data = pickle.dumps(click_data)
            send_data(socket_connection, mouse_click_binary_data)
        else:
            click_data = {'x_coordinate': x_coordinate,
                          'y_coordinate': y_coordinate,
                          'button': str(button)}
            print(f'x : {x_coordinate}')
            print(f'y : {y_coordinate}')
            print(f'button : {button}')
            mouse_click_binary_data = pickle.dumps(click_data)
            send_data(socket_connection, mouse_click_binary_data)

    with Listener(on_click=on_click) as listener:
        listener.join()


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


# def send_screenshot(udp_socket_connection, screenshot_in_binary, ip, port):
#     screenshot_length_in_binary = (1 + len(screenshot_in_binary)).to_bytes(4, byteorder='big')
#     screenshot_in_binary = b'b' + screenshot_in_binary
#
#     try:
#         udp_socket_connection.sendto(screenshot_length_in_binary, (ip, port))
#         udp_socket_connection.sendto(screenshot_in_binary)
#     except ConnectionAbortedError:
#         print(f'> Connection error during data delivering.{ConnectionAbortedError}.')
#
#     except Exception as error:
#         print(f'> Connection error during data delivering.{error}.')
#
#

# def send_screen(socket_connection: socket.socket, ip, port):
#     try:
#         while True:
#             screenshot = get_screenshot()
#             img_buffer = BytesIO()
#             screenshot.save(img_buffer, format='PNG')
#             screenshot_in_binary = img_buffer.getvalue()
#             send_screenshot(socket_connection, screenshot_in_binary, ip, port)
#     finally:
#         socket_connection.close()


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
    time.sleep(5)
    pyautogui.FAILSAFE = False
    pyautogui.mouseDown(x=2560, y=0, button='left')

    # Simulate releasing the right mouse button at the specified position
    pyautogui.mouseUp(x=2560, y=0, button='left')

























