import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def build_url(host: str, port: int) -> str:
    return "http://" + host + ":" + str(port) + "/"
