import os

ABS_PATH = os.path.dirname(os.path.realpath(__file__))


class Configuration(object):
    def __init__(self, **kwargs):
        self.admin_password = os.getenv("CAH_ADMIN_PASSWORD", "admin")
        self.websocket_domain = os.getenv(
            "CAH_WEBSOCKET_DOMAIN", os.getenv("CAH_DOMAIN", "localhost")
        )
        self.server_domain = os.getenv(
            "CAH_SERVER_DOMAIN", os.getenv("CAH_DOMAIN", "localhost")
        )
        self.websocket_port = os.getenv(
            "CAH_WEBSOCKET_PORT", os.getenv("CAH_PORT", 8765)
        )
        self.server_port = os.getenv("CAH_SERVER_PORT", os.getenv("CAH_PORT", 8765))
        self.server_proxy_port = os.getenv(
            "CAH_SERVER_PROXY_PORT", os.getenv("CAH_PORT", 8765)
        )
        self.server_interface = os.getenv("CAH_SERVER_INTERFACE", "")
        self.card_data_path = os.getenv(
            "CAH_CARD_DATA_PATH", os.path.join(ABS_PATH, "data")
        )

    def __getitem__(self, *args, **kwargs):
        return self.__dict__.__getitem__(*args, **kwargs)
