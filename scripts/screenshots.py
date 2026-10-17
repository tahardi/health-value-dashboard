import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "sample.csv"
OUTPUT = ROOT / "docs" / "screenshots"
PORT = 8765
URL = f"http://127.0.0.1:{PORT}"
TIMEOUT = 30


def wait_for_server(url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"waiting for {url} timed out after {timeout} s")


def capture(url: str, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url)
        page.wait_for_selector(".js-plotly-plot .scatterlayer", timeout=TIMEOUT * 1000)
        page.wait_for_selector("#value-table tbody tr", timeout=TIMEOUT * 1000)
        page.screenshot(path=output / "value.png", full_page=True)
        page.get_by_role("tab", name="Data").click()
        page.wait_for_selector("#data-current li", timeout=TIMEOUT * 1000)
        page.wait_for_selector("#data-schema tbody tr", timeout=TIMEOUT * 1000)
        page.screenshot(path=output / "data.png", full_page=True)
        browser.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "sample.csv"
        shutil.copyfile(SAMPLE, data)
        server = subprocess.Popen(
            [sys.executable, "-m", "shiny", "run", "app.app:app", "--port", str(PORT)],
            cwd=ROOT,
            env={**os.environ, "DATA_PATH": str(data)},
        )
        try:
            wait_for_server(URL, TIMEOUT)
            capture(URL, OUTPUT)
        finally:
            server.terminate()
            server.wait()


if __name__ == "__main__":
    main()
