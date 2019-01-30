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
    def open(self):
        self.write_message({
            'type': 'hello'
        })

    def on_message(self, message):
        if message == 'refresh':
            # todo: 获取所有已经启动的 vps && 获取所有可以启动的 vps
            for provider_name, provider_config in config.items():
                if not provider_config['enable']:
                    continue

                self.refresh(provider_name, provider_config)

    def refresh(self, provider_name, provider_config):
        driver = get_driver(getattr(Provider, provider_name))(**provider_config['init_params'])

        nodes = driver.list_nodes()

        pprint(nodes)
        self.write_message({
            'type': 'refresh',
            'nodes': [
                {
                    'uuid': node.uuid,
                    'state': node.state,
                    'public_ips': node.public_ips,
                    'provider_name': provider_name,
                } for node in nodes
            ]
        })


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
