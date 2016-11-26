from tornado import websocket, web, ioloop
from tornado.options import define, options, parse_command_line
import json
import datetime

define("port", default=8887, help="run on the given port", type=int)

USERS = []
ROOMS = []

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

    @staticmethod
    def check_status_game(id_room):
        current_room = []
        for user in USERS:
            if user.get("id_room") == id_room:
                current_room.append(user.get("user"))

        if len(current_room) < 2:
            status = "wait"
            print 'Server message: We have only one user in room ' + str(id_room) + '. Wait...'
            current_room[0].write_message({"status": status})
        else:
            status = "start"
            print 'Server message: We have two players in room ' + str(id_room) + '. Start game.'
            for user in current_room:
                user.write_message({
                    "status": status,
                    "map": maps["map_1"]
                })

    def open(self):
        if self not in USERS:
            self.stream.set_nodelay(True)
            self.timeout = ioloop.IOLoop.current().add_timeout(datetime.timedelta(minutes=60),
                                                               self.explicit_close)
            id_room = self.return_room()
            USERS.append({"id_room": id_room, "user": self})
            self.check_status_game(id_room)

    def on_close(self):
        id_room = None
        for user in USERS:
            if user.get("user") == self:
                id_room = user.get("id_room")
                print 'Server message: User from room ' + str(id_room) + ' was leaved. We need to leave another one.'
                USERS.remove(user)
                break

        for user in USERS:
            if user.get("id_room") == id_room:
                user.get("user").write_message({"status": "close"})
                print 'Server message: User from room ' + str(id_room) + ' was leaved. Room is empty.'
                USERS.remove(user)
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
