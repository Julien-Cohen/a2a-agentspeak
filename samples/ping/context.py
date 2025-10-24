import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def build_url(host: str, port: int) -> str:
    return "http://" + host + ":" + str(port) + "/"


port_sender = 9999
port_receiver = 9998
port_client = 9997
