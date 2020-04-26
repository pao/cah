import os

import yaml

from twisted.application import internet, service
from twisted.web import static, server
from autobahn.resource import WebSocketResource

import pystache
from configuration import Configuration
from caewebsockets import CahServerFactory

WEBROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "www")

config = Configuration()

## Set up the web server
fileResource = static.File(os.path.join(WEBROOT_DIR))
fileResource.indexNames=['index.mustache']

# This is the ugly bit--we need to construct a resource tree to get our templated .js in here
jsResource = static.File(os.path.join(WEBROOT_DIR, "js"))
with open(os.path.join(WEBROOT_DIR, "js", "init.mustache")) as f:
    jsResource.putChild(
        'init.js',
        static.Data(pystache.render(f.read(), config).encode('utf-8'), "application/javascript"),
        )
fileResource.putChild('js', jsResource)

# Serve up websockets
serverURI = "ws://{websocket_domain}:{websocket_port}".format(websocket_domain=config.websocket_domain, websocket_port=config.websocket_port)
cahWampFactory = CahServerFactory(
    serverURI,
    "{server_domain}:{server_port}".format(server_domain=config.server_domain, server_port=config.server_port),
    debug=False,
    debugWamp=True,
    debugCodePaths=False,
    debugApp=False
)
wsResource = WebSocketResource(cahWampFactory)
fileResource.putChild('ws', wsResource)

fileServer = server.Site(fileResource)

## Define the application
application = service.Application("CAH")
internet.TCPServer(
    int(config['server_proxy_port']),
    fileServer,
    interface=config['server_interface']
).setServiceParent(application)
