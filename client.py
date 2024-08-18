# THE CLIENT SIDE WILL RUN ON THE CONTROLLED PC
# THE CLIENT SIDE WILL RUN ON THE CONTROLLED PC
import socket
from PIL import ImageGrab
import pyautogui
import pickle
from helper import get_screen_size, close_socket_connections, send_data, receive_data
import threading
import keyboard
from pynput.mouse import Controller
import numpy as np
import cv2


def convert_pil_image_to_cv2(pil_screen_image):
    cv2_client_screen_image = cv2.cvtColor(np.array(pil_screen_image), cv2.COLOR_RGB2BGR)
    return cv2_client_screen_image


def get_converted_cv2_image_to_binary(cv2_image):
    return pickle.dumps(cv2_image)


def is_screens_equal(current_screen, prior_screen):
    if prior_screen is None:
        return False

    return np.array_equal(current_screen, prior_screen)


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot


def send_screen_shot(client_socket: socket.socket):
    prior_screen = None
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 200000)

    while True:
        screenshot = get_screenshot()
        cv2_screenshot = convert_pil_image_to_cv2(pil_screen_image=screenshot)
        cv2_binary_screenshot = get_converted_cv2_image_to_binary(cv2_screenshot)

        if not is_screens_equal(cv2_binary_screenshot, prior_screen):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, encoded_screenshot_data = cv2.imencode('.jpg', cv2_screenshot, encode_param)
            binary_screenshot_data = np.array(encoded_screenshot_data).tobytes()
            send_data(client_socket, binary_screenshot_data)

        prior_screen = cv2_binary_screenshot


def get_server_screen_size(socket_connection: socket.socket):
    server_screen_size = receive_data(socket_connection)
    server_screen_width, server_screen_height = pickle.loads(server_screen_size)

    return server_screen_width, server_screen_height


def get_screens_ratio(client_screen_width, client_screen_height, server_screen_width, server_screen_height):
    screens_width_ratio = client_screen_width / server_screen_width
    screens_height_ratio = client_screen_height / server_screen_height

    return screens_width_ratio, screens_height_ratio


def get_client_mouse_coordinates(screens_width_ratio, screens_height_ratio, server_x_coordinate, server_y_coordinate):
    client_x_coordinate = int(server_x_coordinate * screens_width_ratio)
    client_y_coordinate = int(server_y_coordinate * screens_height_ratio)

    return client_x_coordinate, client_y_coordinate


def is_server_clicked(first_click_mouse_event, second_click_mouse_event):
    if first_click_mouse_event['x_coordinate'] != second_click_mouse_event['x_coordinate']:
        return False

    if first_click_mouse_event['y_coordinate'] != second_click_mouse_event['y_coordinate']:
        return False

    if first_click_mouse_event['button'] != second_click_mouse_event['button']:
        return False

    return True


def click_mouse(x_coordinate, y_coordinate, button):
    pyautogui.FAILSAFE = False
    x_coordinate = x_coordinate
    y_coordinate = y_coordinate
    button = button
    print(f'mouse click x coordinate {x_coordinate}')
    print(f'mouse click y coordinate {y_coordinate}')
    print(f'Button {button}')
    pyautogui.mouseDown(x=x_coordinate, y=y_coordinate, button=button)


def release_mouse(x_coordinate, y_coordinate, button):
    pyautogui.FAILSAFE = False
    x_coordinate = x_coordinate
    y_coordinate = y_coordinate
    button = button
    print(f'mouse click x coordinate {x_coordinate}')
    print(f'mouse click y coordinate {y_coordinate}')
    print(f'Button {button}')
    pyautogui.mouseUp(x=x_coordinate, y=y_coordinate, button=button)


def handle_mouse_clicks(socket_connection: socket.socket):
    server_screen_width, server_screen_height = get_server_screen_size(socket_connection)
    client_screen_width, client_screen_height = get_screen_size()
    screens_width_ratio, screens_height_ratio = get_screens_ratio(client_screen_width, client_screen_height,
                                                                  server_screen_width, server_screen_height)
    while True:
        print('in the handle mouse clicks while loop ')
        mouse_click_mouse_event = receive_data(socket_connection)
        mouse_click_mouse_event = pickle.loads(mouse_click_mouse_event)

        server_mouse_click_x_coordinate = mouse_click_mouse_event['x_coordinate']
        server_mouse_click_y_coordinate = mouse_click_mouse_event['y_coordinate']

        server_mouse_click_button = mouse_click_mouse_event['button'].split('.')
        server_mouse_click_button = server_mouse_click_button[1]

        client_mouse_click_x_coordinate, client_mouse_click_y_coordinate = get_client_mouse_coordinates(
            screens_width_ratio,
            screens_height_ratio,
            server_mouse_click_x_coordinate,
            server_mouse_click_y_coordinate)

        if mouse_click_mouse_event['pressed']:
            click_mouse(client_mouse_click_x_coordinate, client_mouse_click_y_coordinate, server_mouse_click_button)
        else:
            release_mouse(client_mouse_click_x_coordinate, client_mouse_click_y_coordinate, server_mouse_click_button)


def click_keyboard_button(keyboard_click_event):
    keyboard_key = keyboard_click_event.name
    keyboard.press(keyboard_key)


def release_keyboard_button(keyboard_click_event):
    keyboard_key = keyboard_click_event.name
    keyboard.release(keyboard_key)


def handle_keyboard_clicks(socket_connection: socket.socket):
    while True:
        keyboard_click_event_in_binary = receive_data(socket_connection)
        keyboard_click_event = pickle.loads(keyboard_click_event_in_binary)

        if keyboard_click_event.event_type == 'down':
            click_keyboard_button(keyboard_click_event)
        else:
            release_keyboard_button(keyboard_click_event)


def mouse_scrolling(socket_connection: socket.socket):
    mouse_controller = Controller()
    while True:
        mouse_scroll_data_tuple_in_binary = receive_data(socket_connection)
        mouse_scroll_data_tuple = pickle.loads(mouse_scroll_data_tuple_in_binary)
        x_difference = mouse_scroll_data_tuple[0]
        y_difference = mouse_scroll_data_tuple[1]
        print(f'{x_difference},{y_difference}')
        mouse_controller.scroll(x_difference, y_difference)


def moving_mouse(socket_connection: socket.socket):
    pyautogui.FAILSAFE = False

    server_screen_width, server_screen_height = get_server_screen_size(socket_connection)
    client_screen_width, client_screen_height = get_screen_size()

    screens_width_ratio, screens_height_ratio = get_screens_ratio(client_screen_width, client_screen_height,
                                                                  server_screen_width, server_screen_height)

    try:
        while True:
            server_mouse_coordinates = receive_data(socket_connection)
            server_x_coordinate, server_y_coordinate = pickle.loads(server_mouse_coordinates)

            client_x_coordinate, client_y_coordinate = get_client_mouse_coordinates(screens_width_ratio,
                                                                                    screens_height_ratio,
                                                                                    server_x_coordinate,
                                                                                    server_y_coordinate)
            pyautogui.moveTo(client_x_coordinate, client_y_coordinate)

    except KeyboardInterrupt:
        print(f'{KeyboardInterrupt} while receiving coordinates.')

    except Exception as error:
        print(f'{error} while receiving coordinates.')


def get_client_socket_connections_list(destination_ip, destination_port):
    socket_connections_list = []

    screen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    screen_socket.connect((destination_ip, destination_port))
    socket_connections_list.append(screen_socket)

    mouse_movements_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mouse_movements_socket.connect((destination_ip, destination_port))
    socket_connections_list.append(mouse_movements_socket)

    mouse_clicks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mouse_clicks_socket.connect((destination_ip, destination_port))
    socket_connections_list.append(mouse_clicks_socket)

    mouse_scrolls_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mouse_scrolls_socket.connect((destination_ip, destination_port))
    socket_connections_list.append(mouse_scrolls_socket)

    keyboard_clicks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    keyboard_clicks_socket.connect((destination_ip, destination_port))
    socket_connections_list.append(keyboard_clicks_socket)

    return socket_connections_list


def handle_client_connections(socket_connections_list):
    screen_socket = socket_connections_list[0]
    screen_thread = threading.Thread(target=send_screen_shot, args=(screen_socket,))

    mouse_movements_socket = socket_connections_list[1]
    mouse_movements_thread = threading.Thread(target=moving_mouse, args=(mouse_movements_socket,))

    mouse_clicks_socket = socket_connections_list[2]
    mouse_clicks_thread = threading.Thread(target=handle_mouse_clicks, args=(mouse_clicks_socket,))

    mouse_scrolls_socket = socket_connections_list[3]
    mouse_scrolls_thread = threading.Thread(target=mouse_scrolling, args=(mouse_scrolls_socket,))

    keyboard_clicks_socket = socket_connections_list[4]
    keyboard_clicks_thread = threading.Thread(target=handle_keyboard_clicks, args=(keyboard_clicks_socket,))

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



connections_list = get_client_socket_connections_list('10.100.102.16', 50000)
handle_client_connections(connections_list)
close_socket_connections(connections_list)




























