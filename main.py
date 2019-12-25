import asyncio
import sys

# https://github.com/tornadoweb/tornado/issues/2608
# https://stackoverflow.com/a/58430041
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import json

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path

from abc import ABC
from base64 import b64encode

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from tornado.options import define, options
from tornado_http_auth import DigestAuthMixin, auth_required

define("port", default=8888, help="run on the given port", type=int)
define("config", default='config.json', help="config file path", type=str)
define("username", default='admin', help="http basic auth username", type=str)
define("password", default='admin888', help="http basic auth password", type=str)

tornado.options.parse_command_line()

with open(options.config) as fp:
    config = json.load(fp)

credentials = {options.username: options.password}


# todo: add sys monitor like cloud-torrent
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), (r"/ws", WebSocketHandler)]
        settings = {
            'template_path': os.path.join(os.path.dirname(__file__), "templates"),
            'static_path': os.path.join(os.path.dirname(__file__), "static")
        }
        super(Application, self).__init__(handlers, **settings)


class MainHandler(DigestAuthMixin, tornado.web.RequestHandler, ABC):
    @auth_required(realm='cloud-panel', auth_func=credentials.get)
    def get(self):
        available_providers = {}
        for provider_name, provider_config in config.items():
            if not provider_config['enable']:
                continue

            if 'create_params' not in provider_config:
                continue

            available_providers[provider_name] = provider_config['create_params']

        self.render("index.html", available_providers=available_providers)


class WebSocketHandler(tornado.websocket.WebSocketHandler, ABC):
    def check_origin(self, origin):
        return True

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

            if self.delete(message['provider_name'], message['node_id']):
                self.refresh(message['provider_name'], config[message['provider_name']])
        elif message['type'] == 'create':
            message = message['data']

            if self.create(message['provider_name'], message):
                self.refresh(message['provider_name'], config[message['provider_name']])

    def create(self, provider_name, message):
        driver = get_driver(getattr(Provider, provider_name))(**config[provider_name]['init_params'])

        all_sizes = driver.list_sizes()
        sizes = [each for each in all_sizes if each.id == message['size_id']]

        kwargs = {}

        if provider_name == 'EC2':
            # handle AWS `list_images()` low performance case
            # @see: https://bit.ly/2t263sW
            all_images = driver.list_images(ex_image_ids=[message['image_id']])

            # ex_keyname
            kwargs['ex_keyname'] = message['ex_keyname']
        else:
            all_images = driver.list_images()
        images = [each for each in all_images if each.id == message['image_id']]

        if not sizes or not images:
            return False

        # add driver-spec configs
        kwargs.update(config[provider_name]['create_params']['kwargs'])

        return driver.create_node(
            name='libcloud',
            image=images[0],
            size=sizes[0],
            **kwargs
        )

    def delete(self, provider_name, node_id):
        driver = get_driver(getattr(Provider, provider_name))(**config[provider_name]['init_params'])

        all_nodes = driver.list_nodes()
        nodes = [each for each in all_nodes if each.id == node_id]

        if not nodes:
            return False

        return driver.destroy_node(nodes[0])

    def refresh(self, provider_name, provider_config):
        driver = get_driver(getattr(Provider, provider_name))(**provider_config['init_params'])

        nodes = driver.list_nodes()

        return self.write_message({
            'type': 'refresh',
            'provider_name': provider_name,
            'nodes': [
                {
                    'node_id': node.id,
                    'ss_config': 'ss://{0}#{1}'.format(
                        b64encode('{0}:{1}@{2}:{3}'.format(
                            provider_config['SS_CONFIG']['method'],
                            provider_config['SS_CONFIG']['password'],
                            node.public_ips[0],
                            provider_config['SS_CONFIG']['port']
                        ).encode()).decode(), provider_config['SS_CONFIG']['tag']
                    ) if 'SS_CONFIG' in provider_config and node.public_ips and node.state == 'running' else '',
                    'state': str(node.state),
                    'public_ips': node.public_ips
                } for node in nodes
            ]
        })


def main():
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
