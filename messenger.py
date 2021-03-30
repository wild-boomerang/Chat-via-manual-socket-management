import socket
import threading
import os
import types
import pickle
from datetime import datetime

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65534        # Port to listen on 1-65535 (0 is reserved) (non-privileged ports are > 1023)
BUF_SIZE = 1024
TIME_FORMAT = "%H:%M:%S"
ENCODING = 'UTF-8'


def connect_server(username):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            print('Server is waiting for client connection...')
            conn, addr = s.accept()
            with conn:
                conn.sendall(username.encode(ENCODING))
                interlocutor_name = conn.recv(BUF_SIZE).decode(ENCODING)
                print_success(interlocutor_name)
        return True, addr
    except OSError:
        return False, None


def connect_client(username):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        addr = s.getsockname()
        interlocutor_name = s.recv(BUF_SIZE).decode(ENCODING)
        while username == interlocutor_name:
            username = input('Your interlocutor has the same username. Please, change your username.\n')
        s.sendall(username.encode(ENCODING))
        print_success(interlocutor_name)
    return addr, username


def print_success(interlocutor_name):
    print(f'You are connected to {interlocutor_name}.\n'
          f'To exit from the chat you and your interlocutor should enter an empty string.')


def udp_chat(addr_to_send, own_addr, username):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(own_addr)

    message_pool = []
    input_thread = threading.Thread(target=input_wrapper, args=(udp_sock, addr_to_send, username, message_pool))
    output_thread = threading.Thread(target=output_wrapper, args=(udp_sock, username, message_pool))
    input_thread.start()
    output_thread.start()
    input_thread.join()
    output_thread.join()

    udp_sock.close()


def input_wrapper(s, addr_to_send, username, message_pool):
    print('>>> ', flush=True, end='')

    while True:
        message_content = input()
        data = types.SimpleNamespace(
            addressee=username,
            time=datetime.now(),
            message=message_content,
        )
        s.sendto(pickle.dumps(data), addr_to_send)
        if not message_content:
            break
        message_pool.append(data)
        refresh_chat_output(message_pool, username)


def output_wrapper(s, username, message_pool):
    while True:
        data, _ = s.recvfrom(BUF_SIZE)
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

    own_addr = (HOST, PORT)
    is_connected, addr_to_send = connect_server(username)
    if not is_connected:
        addr_to_send = own_addr
        own_addr, username = connect_client(username)

    udp_chat(own_addr, addr_to_send, username)


if __name__ == '__main__':
    main()
