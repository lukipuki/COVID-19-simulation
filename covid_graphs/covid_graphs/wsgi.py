from os import getenv
from pathlib import Path

from covid_graphs.scripts.server import uswgi_server

data_path = getenv(key="DATA_PATH", default="data")
app = uswgi_server(Path(data_path))

if __name__ == "__main__":
    app.run()
