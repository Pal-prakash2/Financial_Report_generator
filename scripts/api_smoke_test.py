import multiprocessing
import os
import time
from pathlib import Path

import requests
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_IMPORT = "app.main:app"
HOST = "127.0.0.1"
PORT = 8002
SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "sample.xbrl"
OUTPUT_FILE = PROJECT_ROOT / "sample_output.xlsx"


def _run_server() -> None:
    os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))
    config = uvicorn.Config(APP_IMPORT, host=HOST, port=PORT, reload=False, log_level="info")
    server = uvicorn.Server(config)
    server.run()


def main() -> None:
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Sample XBRL file not found at {SAMPLE_FILE}")

    server_process = multiprocessing.Process(target=_run_server, daemon=True)
    server_process.start()
    time.sleep(3)  # Give the server a moment to boot

    with SAMPLE_FILE.open("rb") as fh:
        response = requests.post(
            f"http://{HOST}:{PORT}/api/v1/files/xbrl-to-excel",
            files={"file": (SAMPLE_FILE.name, fh, "application/xml")},
            timeout=30,
        )

    response.raise_for_status()
    OUTPUT_FILE.write_bytes(response.content)

    print(f"Request succeeded with status {response.status_code}")
    print(f"Excel file written to {OUTPUT_FILE} ({len(response.content)} bytes)")

    server_process.terminate()
    server_process.join(timeout=5)


if __name__ == "__main__":
    main()
