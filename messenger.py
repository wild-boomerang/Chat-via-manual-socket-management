import socket
import threading
import os
import types
import pickle
from datetime import datetime

HOST = '127.0.0.1'
PORT = 65432
BUF_SIZE = 1024
TIME_FORMAT = "%H:%M:%S"


def server(username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()  # may be set 1?
            print('Server is listening and waiting for client connection...')
            conn, addr = s.accept()
            with conn:
                chat(conn, username)

        return True
    except OSError:
        return False


def client(username):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        chat(s, username)


def chat(s, username):
    message_pool = []
    input_thread = threading.Thread(target=input_wrapper, args=(s, username, message_pool))
    output_thread = threading.Thread(target=output_wrapper, args=(s, username, message_pool))
    input_thread.start()
    output_thread.start()
    input_thread.join()
    output_thread.join()


def input_wrapper(s, username, message_pool):
    print('>>> ', flush=True, end='')

    while True:
        message_content = input()
        data = types.SimpleNamespace(
            addressee=username,
            time=datetime.now(),
            message=message_content,
        )
        s.sendall(pickle.dumps(data))
        if not message_content:
            break
        message_pool.append(data)
        refresh_chat_output(message_pool, username)


def output_wrapper(s, username, message_pool):
    while True:
        data = s.recv(BUF_SIZE)
        message_item = pickle.loads(data)
        if not message_item.message:
            break
        message_pool.append(message_item)
        refresh_chat_output(message_pool, username)


def refresh_chat_output(message_pool, username):
    clear_console_output()
    for message_item in sorted(message_pool, key=lambda elem: elem.time):
        message_time = message_item.time.strftime(TIME_FORMAT)
        addressee = 'me' if message_item.addressee == username else message_item.addressee
        print(f'{addressee} at {message_time}: {message_item.message}')
    print('>>> ', flush=True, end='')


def clear_console_output():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    username = str(input('Choose your name: '))

    is_connected = server(username)
    if not is_connected:
        client(username)


if __name__ == '__main__':
    main()
