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

    def on_message(self, raw_message):
        message = json.loads(raw_message)

        if message['type'] == 'refresh':
            for provider_name, provider_config in config.items():
                if not provider_config['enable']:
                    continue

                self.refresh(provider_name, provider_config)
        elif message['type'] == 'delete':
            message = message['data']

            if self.delete(message['node_id'], message['provider_name']):
                self.refresh(message['provider_name'], config[message['provider_name']])

    def delete(self, node_id, provider_name):
        return get_driver(getattr(Provider, provider_name)) \
            (**config[provider_name]['init_params']) \
            .destroy_node(type('obj', (object,), {'id': node_id}))

    def refresh(self, provider_name, provider_config):
        driver = get_driver(getattr(Provider, provider_name))(**provider_config['init_params'])

        nodes = driver.list_nodes()

        return self.write_message({
            'type': 'refresh',
            'provider_name': provider_name,
            'nodes': [
                {
                    'node_id': node.id,
                    'state': node.state,
                    'public_ips': node.public_ips
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
