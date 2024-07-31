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
    mouse_thread = threading.Thread(target=send_server_mouse_coordinates, args=(mouse_socket,))

    screen_thread.start()
    mouse_thread.start()

    screen_thread.join()
    mouse_thread.join()


def get_sockets_connections_list(server_socket: socket.socket):
    socket_connections_list = []

    screen_socket, client_address = server_socket.accept()
    socket_connections_list.append(screen_socket)

    mouse_movements_socket, client_address = server_socket.accept()
    socket_connections_list.append(mouse_movements_socket)

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
