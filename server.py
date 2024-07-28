# THE SERVER SIDE WILL RUN ON THE CONTROLLING PC
from PIL import Image
import socket
from io import BytesIO
import numpy as np
from helper import receive_data, send_data, get_screen_size
import cv2
import pyautogui
import pickle
import time
import threading

SERVER_BINDING_IP = '0.0.0.0'
SERVER_PORT = 50000


def send_server_mouse_coordinates(socket_connection: socket.socket):
    server_screen_width, server_screen_height = get_screen_size()
    server_screen_size_in_binary = pickle.dumps((server_screen_width, server_screen_height))
    send_data(socket_connection, server_screen_size_in_binary)
    try:
        while True:
            x_coordinate, y_coordinate = pyautogui.position()
            print(f'server coordinates are {x_coordinate},{y_coordinate}')
            coordinates_in_binary = pickle.dumps((x_coordinate, y_coordinate))
            send_data(socket_connection, coordinates_in_binary)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f'{KeyboardInterrupt} while sending coordinates.')
    except Exception as error:
        print(f'{error} while sending coordinates.')


def display_client_screen(client_socket: socket.socket):
    screen_width, screen_height = get_screen_size()
    screen_height = screen_height - 80
    while True:
        image_binary_data = receive_data(client_socket)
        if image_binary_data:
            try:
                pil_image = Image.open(BytesIO(image_binary_data))
                cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2_image_in_screen_size = cv2.resize(cv2_image, (screen_width, screen_height))
                cv2.imshow('CONTROLLED PC SCREEN', cv2_image_in_screen_size)
            except OSError:
                print(f'Invalid image.{OSError}.')
            except Exception as error:
                print(f'Error with displaying the client screen.{error}.')

            if cv2.waitKey(1) == ord('q'):
                break


def handle_client(client_socket: socket.socket):
    mouse_thread = threading.Thread(target=send_server_mouse_coordinates, args=(client_socket,))
    screen_thread = threading.Thread(target=display_client_screen, args=(client_socket,))

    #display_client_screen(client_socket)
    #send_server_mouse_coordinates(client_socket)
    mouse_thread.start()
    screen_thread.start()
    mouse_thread.join()
    screen_thread.join()

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

    client_socket, client_address = server_socket.accept()
    print(f'> Server got connection from {client_address}')

    handle_client(client_socket)

    client_socket.close()
    cv2.destroyAllWindows()


running_server_on_tcp_socket(SERVER_BINDING_IP, SERVER_PORT)

#Error with displaying the client screen.only integer scalar arrays can be converted to a scalar index.
# if __name__ == '__main__':
#     while True:
#         print(pyautogui.position())
