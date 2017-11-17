import threading
from hashlib import md5
import collections
import socket
import Queue
import sys


class ThreadManager(threading.Thread):
    def __init__(self, in_connections):
        threading.Thread.__init__(self)
        self.in_connections = in_connections

    def run(self):
        while True:
            socket, address = self.in_connections.get()
            single_connection(socket, address)
            self.in_connections.task_done()

def single_connection(socket, address):
    while True:
        input = socket.recv(2048).decode('utf-8')
        if input.startswith("KILL_SERVICE"):
            socket.close()
            break

        elif input.startswith("HELO"):
            socket.sendall("{0}\nIP:{1}\nPORT:{2}\nStudentID:{3}".format(input.strip(), "134.226.32.10", str(address[1]), "12326755"))
            continue

        input = input.split('\n')
        action_key_value = input[0]
        action = action_key_value[:action_key_value.find(':')]
        
        if (action == 'JOIN_CHATROOM'):
            client_name = input[3].split(":")[1]
            room_name = input[0].split(":")[1]
            room_identifier = int(md5(room_name).hexdigest(), 16)
            room_join_id = int(md5(client_name).hexdigest(), 16)
            if room_identifier not in rooms:
                rooms[room_identifier] = dict()
            if room_join_id not in rooms[room_identifier]:
                rooms[room_identifier][room_join_id] = socket
                socket.sendall("JOINED_CHATROOM:{0}\nSERVER_IP:{1}\nPORT:{2}\nROOM_REF:{3}\nJOIN_ID:{4}\n".format(str(room_name), address[0], address[1], str(room_identifier), str(room_join_id)))
                broadcast(room_identifier, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}".format(str(room_identifier), str(client_name), str(client_name) + " has joined this chatroom.\n\n"))
        elif (action == 'CHAT'):
            room_id = int(input[0].split(":")[1])
            room_join_id = int(input[1].split(":")[1])
            client_name = input[2].split(":")[1]
            broadcast(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), input[3].split(":")[1]))

        elif (action == 'LEAVE_CHATROOM'):
            room_id = int(input[0].split(":")[1])
            room_join_id = int(input[1].split(":")[1])
            client_name = input[2].split(":")[1]
            socket.sendall("LEFT_CHATROOM:{0}\nJOIN_ID:{1}\n".format(str(room_id), str(room_join_id)))
            broadcast(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), str(client_name) + " has left this chatroom."))
            del rooms[room_id][room_join_id]

        elif (action == 'DISCONNECT'):
            client_name = input[2].split(":")[1]
            room_join_id = int(md5(client_name).hexdigest(), 16)
            for room_id in rooms.keys():
                if room_join_id in rooms[room_id]:
                    broadcast(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), str(client_name) + " has left this chatroom."))
                    if room_join_id in rooms[room_id]:
                        del rooms[room_id][room_join_id]
            break

def broadcast(room_id, input):
    for room_join_id, connection in rooms[room_id].iteritems():
        connection.sendall(input)

in_connections = Queue.Queue(maxsize=100)
rooms = collections.OrderedDict()
sockets = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ipadd = socket.gethostbyname(socket.gethostname())
sockets.bind((ipadd, sys.argv[1]))
sockets.listen(5)

while True:
    connection, address = sockets.accept()
    connection_handler = ThreadManager(in_connections)
    connection_handler.setDaemon(True)
    connection_handler.start()
    in_connections.put((connection, address))
