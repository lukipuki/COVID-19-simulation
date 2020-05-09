from os import getenv
from pathlib import Path

from .server import setup_server

data_path = Path(getenv(key="DATA_PATH", default="data"))
app = setup_server(data_path, data_path / "predictions")

if __name__ == "__main__":
    app.run()
