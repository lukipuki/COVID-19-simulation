from os import getenv
from pathlib import Path

from .server import setup_server

data_path = getenv(key="DATA_PATH", default="data")
app = setup_server(Path(data_path))

if __name__ == "__main__":
    app.run()
