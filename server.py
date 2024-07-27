# THE SERVER SIDE WILL RUN ON THE CONTROLLING PC
from PIL import Image
import socket
from io import BytesIO
import numpy as np
from helper import receive_data, send_data
import cv2

SERVER_BINDING_IP = '0.0.0.0'
SERVER_PORT = 50000
BINDING_IP = '0.0.0.0'


def display_client_screen(client_socket: socket.socket):
    while True:
        image_binary_data = receive_data(client_socket)
        if image_binary_data:
            try:
                pil_image = Image.open(BytesIO(image_binary_data))
                cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                cv2.imshow('CONTROLLED PC SCREEN', cv2_image)
            except OSError:
                print(f'Invalid image.{OSError}.')
            except Exception as error:
                print(f'Error with displaying the client screen.{error}.')

            if cv2.waitKey(1) == ord('q'):
                break


def handle_client(client_socket: socket.socket):
    display_client_screen(client_socket)


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

