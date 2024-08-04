# THE CLIENT SIDE WILL RUN ON THE CONTROLLED PC
import socket
from io import BytesIO
from PIL import ImageGrab
import pyautogui
import pickle
from helper import get_screen_size, close_socket_connections, send_data, receive_data
import threading
import keyboard


def get_screenshot():
    screenshot = ImageGrab.grab()
    return screenshot


def send_screen_shot(client_socket: socket.socket):
    try:
        while True:
            screenshot = get_screenshot()
            img_buffer = BytesIO()
            screenshot.save(img_buffer, format='PNG')
            screenshot_in_binary = img_buffer.getvalue()
            send_data(client_socket, screenshot_in_binary, is_text=False)
    finally:
        client_socket.close()


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


def execute_mouse_click(x_coordinate, y_coordinate, button):
    pyautogui.FAILSAFE = False
    x_coordinate = x_coordinate
    y_coordinate = y_coordinate
    button = button
    print(f'mouse click x coordinate {x_coordinate}')
    print(f'mouse click y coordinate {y_coordinate}')
    print(f'Button {button}')
    pyautogui.click(x_coordinate, y_coordinate, button=button)


def handle_mouse_clicks(socket_connection: socket.socket):
    server_screen_width, server_screen_height = get_server_screen_size(socket_connection)
    client_screen_width, client_screen_height = get_screen_size()
    screens_width_ratio, screens_height_ratio = get_screens_ratio(client_screen_width, client_screen_height,
                                                                  server_screen_width, server_screen_height)
    while True:
        first_click_mouse_event = receive_data(socket_connection)
        first_click_mouse_event = pickle.loads(first_click_mouse_event)
        second_click_mouse_event = receive_data(socket_connection)
        second_click_mouse_event = pickle.loads(second_click_mouse_event)

        if is_server_clicked(first_click_mouse_event, second_click_mouse_event):
            server_mouse_click_x_coordinate = first_click_mouse_event['x_coordinate']
            server_mouse_click_y_coordinate = first_click_mouse_event['y_coordinate']

            client_mouse_click_x_coordinate, client_mouse_click_y_coordinate = get_client_mouse_coordinates(screens_width_ratio,
                                                                                                            screens_height_ratio,
                                                                                                            server_mouse_click_x_coordinate,
                                                                                                            server_mouse_click_y_coordinate)
            print(f'{client_mouse_click_x_coordinate},{client_mouse_click_y_coordinate}')
            button = first_click_mouse_event['button'].split('.')
            button = button[1]
            #execute_mouse_click(mouse_click_data=first_click_mouse_event)
            execute_mouse_click(client_mouse_click_x_coordinate, client_mouse_click_y_coordinate, button)


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

    keyboard_clicks_socket = socket_connections_list[3]
    keyboard_clicks_thread = threading.Thread(target=handle_keyboard_clicks, args=(keyboard_clicks_socket,))

    screen_thread.start()
    mouse_movements_thread.start()
    mouse_clicks_thread.start()
    keyboard_clicks_thread.start()

    screen_thread.join()
    mouse_movements_thread.join()
    mouse_clicks_thread.join()
    keyboard_clicks_thread.join()


connections_list = get_client_socket_connections_list('10.100.102.16', 50000)
handle_client_connections(connections_list)
close_socket_connections(connections_list)

# my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# my_socket.connect(('10.100.102.16', 50000))
# send_screen_shot(my_socket)
# screen_thread = threading.Thread(target=send_screen_shot, args=(my_socket,))
# receive_server_mouse_coordinates(socket_connection=my_socket)

# mouse_thread = threading.Thread(target=receive_server_mouse_coordinates, args=(my_socket,))
# screen_thread.start()
# mouse_thread.start()

# screen_thread.join()
# mouse_thread.join()
