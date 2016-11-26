from tornado import websocket, web, ioloop
from tornado.options import define, options, parse_command_line
import json
import datetime

define("port", default=5000, help="run on the given port", type=int)

cl = []

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
        [12, 13, 14, 16, 21, 24, 25, 27, 31, 36, 41, 42, 46, 47, 52,
            57, 61, 63, 64, 47, 68, 72, 74, 75, 76, 79, 86, 89, 97, 98],
        ["blue", "red", "red", "empty", "blue", "blue", "red", "red", "blue"]
    ],
    "map_4": [
        [12, 14, 17, 21, 23, 24, 25, 26, 32, 36, 39, 41, 42, 45, 47, 48, 52, 54,
            56, 58, 62, 63, 65, 68, 69, 71, 74, 78, 84, 85, 86, 87, 89, 93, 96, 98],
        ["red", "red", "blue", "red", "empty", "blue", "red", "blue", "blue"]
    ]
}


class IndexHandler(web.RequestHandler):
    def get(self):
        print cl
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def check_length(self):
        print '!!!'
        if (len(cl) < 2):
            print 'Length of clients less than two'
            cl[0].write_message({"status": "wait"})
        else:
            print 'Send map / start game'
            for c in cl:
                c.write_message({
                    "map": maps["map_1"]
                })

    def open(self):
        print 'OPEN!'
        if self not in cl:
            self.stream.set_nodelay(True)
            self.timeout = ioloop.IOLoop.current().add_timeout(datetime.timedelta(minutes=60), self.explicit_close)
            cl.append(self)
            self.check_length()

    def on_close(self):
        if self in cl:
            cl.remove(self)

    def explicit_close(self):
        self.close()


class ApiHandler(web.RequestHandler):
    @web.asynchronous
    def get(self, *args):
        print 'Get value'
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id": id, "value": value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        print 'Post value'
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id": id, "value": value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    ioloop.IOLoop.instance().start()
