# THE SERVER SIDE WILL RUN ON THE CONTROLLING PC
from PIL import Image
import socket
from io import BytesIO
import numpy as np
from helper import receive_data, send_data, get_screen_size, is_mouse_change_coordinates, close_socket_connections
import cv2
import pyautogui
import pickle
import time
import threading
from pynput.mouse import Listener
import keyboard

SERVER_BINDING_IP = '0.0.0.0'
SERVER_PORT = 50000


def convert_binary_to_cv2_image(binary_data):
    pil_screen_image = Image.open(BytesIO(binary_data))
    cv2_client_screen_image = cv2.cvtColor(np.array(pil_screen_image), cv2.COLOR_RGB2BGR)

    return cv2_client_screen_image


def setup_window_properties(window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def display_cv2_image(window_name, image):
    cv2.imshow(window_name, image)


def send_mouse_click_data(socket_connection: socket.socket):
    send_screen_size(socket_connection)

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


def send_mouse_scrolls_data(socket_connection: socket.socket):
    def on_scroll(x_coordinate, y_coordinate, x_difference, y_difference):
        mouse_scroll_data_tuple = (x_difference, y_difference)
        mouse_scroll_data_tuple_in_binary = pickle.dumps(mouse_scroll_data_tuple)
        send_data(socket_connection, mouse_scroll_data_tuple_in_binary)

        print(mouse_scroll_data_tuple)

    with Listener(on_scroll=on_scroll) as listener:
        listener.join()


def send_keyboard_clicks(socket_connection: socket.socket):
    while True:
        keyboard_click_event = keyboard.read_event()
        keyboard_click_event_in_binary = pickle.dumps(keyboard_click_event)
        send_data(socket_connection, keyboard_click_event_in_binary)


def send_screen_size(socket_connection: socket.socket):
    server_screen_width, server_screen_height = get_screen_size()
    server_screen_size_tuple_in_binary = pickle.dumps((server_screen_width, server_screen_height))
    send_data(socket_connection, server_screen_size_tuple_in_binary)


def send_server_mouse_coordinates(socket_connection: socket.socket):
    send_screen_size(socket_connection)
    prior_x_coordinate = -1
    prior_y_coordinate = -1
    try:
        while True:
            x_coordinate, y_coordinate = pyautogui.position()
            if is_mouse_change_coordinates(x_coordinate, y_coordinate, prior_x_coordinate, prior_y_coordinate):
                print(f'server coordinates are {x_coordinate},{y_coordinate}')
                coordinates_tuple_in_binary = pickle.dumps((x_coordinate, y_coordinate))
                send_data(socket_connection, coordinates_tuple_in_binary)

            time.sleep(0.1)
            prior_x_coordinate = x_coordinate
            prior_y_coordinate = y_coordinate

    except KeyboardInterrupt:
        print(f'{KeyboardInterrupt} while sending coordinates.')

    except Exception as error:
        print(f'{error} while sending coordinates.')


def display_client_screen(client_socket: socket.socket):
    while True:
        client_screen_in_binary = receive_data(client_socket)
        if client_screen_in_binary:
            try:
                cv2_client_screen_image = convert_binary_to_cv2_image(binary_data=client_screen_in_binary)
                setup_window_properties(window_name='CONTROLLED PC SCREEN')
                display_cv2_image(window_name='CONTROLLED PC SCREEN', image=cv2_client_screen_image)

            except OSError:
                print(f'Invalid image.{OSError}.')

            except Exception as error:
                print(f'Error with displaying the client screen.{error}.')

            if cv2.waitKey(1) == ord('q'):
                break

            time.sleep(0.05)


def handle_client_connections(socket_connections_list):
    screen_socket = socket_connections_list[0]
    screen_thread = threading.Thread(target=display_client_screen, args=(screen_socket,))

    mouse_socket = socket_connections_list[1]
    mouse_movements_thread = threading.Thread(target=send_server_mouse_coordinates, args=(mouse_socket,))

    mouse_clicks_socket = socket_connections_list[2]
    mouse_clicks_thread = threading.Thread(target=send_mouse_click_data, args=(mouse_clicks_socket,))

    mouse_scrolls_socket = socket_connections_list[3]
    mouse_scrolls_thread = threading.Thread(target=send_mouse_scrolls_data, args=(mouse_scrolls_socket,))

    keyboard_clicks_socket = socket_connections_list[4]
    keyboard_clicks_thread = threading.Thread(target=send_keyboard_clicks, args=(keyboard_clicks_socket,))

    screen_thread.start()
    mouse_movements_thread.start()
    mouse_clicks_thread.start()
    mouse_scrolls_thread.start()
    keyboard_clicks_thread.start()

    screen_thread.join()
    mouse_movements_thread.join()
    mouse_clicks_thread.join()
    mouse_scrolls_thread.join()
    keyboard_clicks_thread.join()


def get_sockets_connections_list(server_socket: socket.socket):
    socket_connections_list = []

    screen_socket, _ = server_socket.accept()
    socket_connections_list.append(screen_socket)

    mouse_movements_socket, _ = server_socket.accept()
    socket_connections_list.append(mouse_movements_socket)

    mouse_clicks_socket, _ = server_socket.accept()
    socket_connections_list.append(mouse_clicks_socket)

    mouse_scrolls_socket, _ = server_socket.accept()
    socket_connections_list.append(mouse_scrolls_socket)

    keyboard_clicks_socket, _ = server_socket.accept()
    socket_connections_list.append(keyboard_clicks_socket)

    return socket_connections_list


def running_server_on_tcp_socket(server_binding_ip, port_number, number_of_listeners=1):
    """
    This function running server on tcp socket. This server has the ability to serve
    multiple amount of clients, server do it by using the multithreading method.
    :param server_binding_ip:
    :param port_number:
    :param number_of_listeners:
    :return None:
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_binding_ip, port_number))
    server_socket.listen(number_of_listeners)
    print(f'> Server is up and running on ip : {server_binding_ip} and port : {port_number}.')

    socket_connections_list = get_sockets_connections_list(server_socket)
    handle_client_connections(socket_connections_list)

    print(f'> Server got connection !!!')

    close_socket_connections(socket_connections_list)
    cv2.destroyAllWindows()


running_server_on_tcp_socket(SERVER_BINDING_IP, SERVER_PORT)

# if __name__ == '__main__':
#     while True:
#         print(pyautogui.position())
