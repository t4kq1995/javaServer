from tornado import websocket, web, ioloop
from tornado.options import define, options, parse_command_line
import json
import datetime
import ast

define("port", default=8887, help="run on the given port", type=int)

USERS = []
ROOMS = []
ROOM_NUMBER = 1

maps = {
    "map_1": [
        [13, 14, 23, 25, 31, 32, 34, 35, 41, 43, 45, 52, 53, 54],
        ["red", "red", "empty", "blue", "blue"]
    ],
    "map_2": [
        [12, 13, 14, 16, 21, 24, 25, 27, 31, 36, 41, 42,
            46, 47, 52, 57, 61, 63, 64, 67, 72, 74, 75, 76],
        ["blue", "blue", "red", "empty", "blue", "red", "red"]
    ],
    "map_2_1": [
        [13, 14, 16, 24, 25, 27, 31, 36, 41, 42, 46,
            47, 52, 57, 61, 63, 64, 67, 72, 74, 75, 76],
        ["blue", "blue", "red", "empty", "blue", "red", "red"]
    ],
    "map_3": [
        [12, 14, 17, 21, 23, 24, 25, 26, 32, 36, 39, 41, 42, 45, 47, 48, 52, 54,
            56, 58, 62, 63, 65, 68, 69, 71, 74, 78, 84, 85, 86, 87, 89, 93, 96, 98],
        ["red", "red", "blue", "red", "empty", "blue", "red", "blue", "blue"]
    ]
}


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def on_message(self, message):
        global ROOM_NUMBER
        message = ast.literal_eval(message)
        if message.get("status") == "map":
            if ROOM_NUMBER == 1:
                USERS.append({"id_room": ROOM_NUMBER, "user": self, "color": "red"})
                ROOMS.append({"id_room": ROOM_NUMBER, "map": message.get("map"), "users": 1})
                ROOM_NUMBER += 1
                self.write_message({"status": "wait"})
                print 'Server message: we notice new room ' + str(ROOM_NUMBER - 1)
            else:
                was_find = False
                for room in ROOMS:
                    if room.get("map") == message.get("map") and room.get("users") != 2:
                        was_find = True
                        USERS.append({"id_room": room.get("id_room"), "user": self, "color": "blue"})
                        room["users"] = 2
                        for user in USERS:
                            if user.get("id_room") == room.get("id_room"):
                                user.get("user").write_message({
                                    "status": "start",
                                    "map": maps["map_" + str(room.get("map"))]
                                })
                        print 'Server message: game start for room ' + str(room.get("id_room"))
                        break
                if was_find is False:
                    USERS.append({"id_room": ROOM_NUMBER, "user": self, "color": "red"})
                    ROOMS.append({"id_room": ROOM_NUMBER, "map": message.get("map"), "users": 1})
                    ROOM_NUMBER += 1
                    self.write_message({"status": "wait"})
        else:
            id_room = None
            for user in USERS:
                if user.get("user") == self:
                    id_room = user.get("id_room")
                    break

            for user in USERS:
                if user.get("user") != self and user.get("id_room") == id_room:
                    print 'Server message : user from room ' + str(id_room) + ' was sent interesting message.'
                    user.get("user").write_message(message)

    @staticmethod
    def return_room():
        return int(round(float(len(USERS) + 1.0) / 2.0))

    def open(self):
        if self not in USERS:
            self.stream.set_nodelay(True)
            self.timeout = ioloop.IOLoop.current().add_timeout(datetime.timedelta(minutes=60),
                                                               self.explicit_close)
            print 'Server message: We notice new connection'

    def on_close(self):
        id_room = None
        color = None
        for user in USERS:
            if user.get("user") == self:
                id_room = user.get("id_room")
                color = user.get("color")
                print 'Server message: User from room ' + str(id_room) + ' was leaved. We need to leave another one.'
                USERS.remove(user)
                break

        for user in USERS:
            if user.get("id_room") == id_room:
                user.get("user").write_message({"status": "close", "color": color})
                print 'Server message: User from room ' + str(id_room) + ' was leaved. Room is empty.'
                USERS.remove(user)
                break

        for room in ROOMS:
            if room.get("id_room") == id_room:
                ROOMS.remove(room)
                break

    def explicit_close(self):
        self.close()


app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    ioloop.IOLoop.instance().start()
