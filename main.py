import json

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path

from abc import ABC
from sys import argv

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from tornado.options import define, options
from pprint import pprint

define("port", default=8888, help="run on the given port", type=int)
DEFAULT_CONFIG_FILE = 'config.json'

with open(argv[1] if len(argv) > 1 else DEFAULT_CONFIG_FILE) as fp:
    config = json.load(fp)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), (r"/ws", WebSocketHandler)]
        settings = {
            'template_path': os.path.join(os.path.dirname(__file__), "templates"),
            'static_path': os.path.join(os.path.dirname(__file__), "static")
        }
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render("index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler, ABC):
    def on_message(self, message):
        if message == 'refresh':
            # todo: 获取所有已经启动的 vps && 获取所有可以启动的 vps
            for provider_name, provider_config in config.items():
                if not provider_config['enable']:
                    continue

                driver = get_driver(getattr(Provider, provider_name))(**provider_config['init_params'])

                pprint(driver.list_nodes())

            return self.write_message('refreshing')
        return self.write_message(u"You said: " + message)


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
