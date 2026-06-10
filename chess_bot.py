import sys
import os
import json
import platform
import subprocess
import urllib.request
import zipfile
import io
from time import sleep
from DrissionPage import ChromiumPage, ChromiumOptions
from stockfish import Stockfish
from colorama import Fore, init as colorama_init

colorama_init(autoreset=True)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CheatBot:
    def __init__(self, stockfish_path=None, browser_path=None):
        self.stockfish_path = (
            stockfish_path
            if stockfish_path and os.path.exists(stockfish_path)
            else None
        )
        if not self.stockfish_path:
            self.stockfish_path = self._auto_detect_stockfish()
        if not self.stockfish_path:
            self.stockfish_path = self._download_stockfish()

        self.browser_path = (
            browser_path if browser_path and os.path.exists(browser_path) else None
        )
        if not self.browser_path:
            self.browser_path = self._auto_detect_browser()

        self.depth = 9
        self.accounts_file = "acc.json"
        self.session_file = "session.json"
        self.username = None
        self.password = None
        self.page = None

    def _auto_detect_stockfish(self):
        system = platform.system()
        if system == "Windows":
            candidates = [
                resource_path("stockfish-windows-x86-64-avx2.exe"),
                "stockfish.exe",
                r"C:\Program Files\Stockfish\stockfish.exe",
            ]
        else:
            candidates = [
                "stockfish",
                "/usr/games/stockfish",
                "/usr/local/bin/stockfish",
            ]
        for candidate in candidates:
            if os.path.exists(candidate):
                print(Fore.GREEN + f"✓ Found Stockfish at {candidate}" + Fore.RESET)
                return candidate
        return None

    def _download_stockfish(self):
        system = platform.system()
        print(Fore.CYAN + "→ Stockfish not found, downloading..." + Fore.RESET)
        try:
            if system == "Windows":
                url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip"
                exe_name = "stockfish-windows-x86-64-avx2.exe"
            elif system == "Linux":
                url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64.zip"
                exe_name = "stockfish-ubuntu-x86-64"
            else:
                print(Fore.RED + "✗ Unsupported OS for auto-download" + Fore.RESET)
                return None

            with urllib.request.urlopen(url) as resp:
                with zipfile.ZipFile(io.BytesIO(resp.read())) as z:
                    z.extract(exe_name, path=".")
            os.chmod(exe_name, 0o755)
            dest = resource_path(exe_name)
            if dest != exe_name:
                os.rename(exe_name, dest)
            print(Fore.GREEN + f"✓ Stockfish downloaded to {dest}" + Fore.RESET)
            return dest
        except Exception as e:
            print(Fore.RED + f"✗ Download failed: {e}" + Fore.RESET)
            return None

    def _auto_detect_browser(self):
        system = platform.system()
        if system == "Windows":
            candidates = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ]
        else:
            candidates = [
                "brave-browser",
                "google-chrome",
                "chromium-browser",
                "chromium",
                "microsoft-edge",
            ]
        for candidate in candidates:
            if os.path.exists(candidate) or (
                system != "Windows"
                and subprocess.call(
                    f"which {candidate}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                == 0
            ):
                print(Fore.GREEN + f"✓ Detected browser: {candidate}" + Fore.RESET)
                return candidate
        print(
            Fore.YELLOW + "⚠ No browser found, using DrissionPage default" + Fore.RESET
        )
        return None

    def cleanup(self):
        if self.page:
            try:
                self.page.quit()
            except:
                pass
            self.page = None

    def load_credentials(self):
        try:
            with open(self.accounts_file, "r") as f:
                data = json.load(f)
                self.username = data.get("username")
                self.password = data.get("pass")
            if not self.username or not self.password:
                raise ValueError("Missing username or password in acc.json")
            print(Fore.GREEN + "✓ Credentials loaded" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"✗ Failed to load credentials: {e}" + Fore.RESET)
            self.kill("credentials_error")

    def kill(self, reason=""):
        print(Fore.RED + f"Killed: {reason}" + Fore.RESET)
        self.cleanup()
        sys.exit(1)

    def init_stockfish(self):
        if not self.stockfish_path or not os.path.exists(self.stockfish_path):
            print(Fore.RED + "✗ Stockfish not available" + Fore.RESET)
            return None
        try:
            sf = Stockfish(path=self.stockfish_path)
            sf.set_depth(self.depth)
            print(Fore.GREEN + "✓ Stockfish engine ready" + Fore.RESET)
            return sf
        except Exception as e:
            print(Fore.RED + f"✗ Stockfish init error: {e}" + Fore.RESET)
            return None

    def init_browser(self):
        try:
            options = ChromiumOptions()
            if self.browser_path:
                options.set_browser_path(self.browser_path)
            options.auto_port()
            options.set_argument("--disable-gpu")
            options.set_argument("--window-size=1280,720")
            self.page = ChromiumPage(options)
            print(Fore.GREEN + "✓ Browser launched" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"✗ Browser init error: {e}" + Fore.RESET)
            self.kill("browser_init_error")

    def accept_cookies(self):
        try:
            if self.page.wait.ele_displayed(
                'xpath://button[text()="Allow all cookies"]', timeout=2
            ):
                btn = self.page.ele('xpath://button[text()="Allow all cookies"]')
                btn.click()
                print(Fore.CYAN + "→ Accepted cookies" + Fore.RESET)
        except:
            pass

    def save_session(self):
        print(Fore.CYAN + "→ Saving session..." + Fore.RESET)
        try:
            cookies = self.page.cookies()
            local_storage = self.page.run_js("return window.localStorage;")
            session_storage = self.page.run_js("return window.sessionStorage;")
            data = {
                "cookies": cookies,
                "local_storage": dict(local_storage) if local_storage else {},
                "session_storage": dict(session_storage) if session_storage else {},
            }
            with open(self.session_file, "w") as f:
                json.dump(data, f, indent=4)
            print(Fore.GREEN + "✓ Session saved" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"✗ Failed to save session: {e}" + Fore.RESET)

    def load_session(self, url):
        if not os.path.exists(self.session_file):
            return False
        print(Fore.CYAN + "→ Loading saved session..." + Fore.RESET)
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            self.page.get(url)
            if "cookies" in data:
                self.page.set.cookies(data["cookies"])
            if "local_storage" in data:
                for k, v in data["local_storage"].items():
                    self.page.run_js(
                        "window.localStorage.setItem(arguments[0], arguments[1]);", k, v
                    )
            if "session_storage" in data:
                for k, v in data["session_storage"].items():
                    self.page.run_js(
                        "window.sessionStorage.setItem(arguments[0], arguments[1]);",
                        k,
                        v,
                    )
            self.page.refresh()
            sleep(2)
            if not self.page.ele('xpath://input[@id="login-username"]', timeout=2):
                print(
                    Fore.GREEN + "✓ Session restored (already logged in)" + Fore.RESET
                )
                return True
            else:
                print(
                    Fore.YELLOW + "⚠ Session expired, will log in manually" + Fore.RESET
                )
                return False
        except Exception as e:
            print(Fore.RED + f"✗ Session load error: {e}" + Fore.RESET)
            return False

    def login(self):
        self.load_credentials()
        url = "https://www.chess.com/login_and_go"
        if self.load_session(url):
            return
        self.page.get(url)
        self.accept_cookies()
        try:
            if self.page.wait.ele_displayed(
                'xpath://input[@id="login-username"]', timeout=5
            ):
                username_input = self.page.ele('xpath://input[@id="login-username"]')
                password_input = self.page.ele('xpath://input[@id="login-password"]')
                login_button = self.page.ele('xpath://button[@id="login"]')
                username_input.input(self.username)
                sleep(0.5)
                password_input.input(self.password)
                sleep(0.5)
                current_url = self.page.url
                login_button.click()
                print(Fore.YELLOW + "→ Waiting for login to complete..." + Fore.RESET)
                self.page.wait.url_change(current_url, exclude=True, timeout=15)
                self.save_session()
                print(Fore.GREEN + "✓ Login successful, session saved" + Fore.RESET)
            else:
                raise Exception("Login form not found")
        except Exception as e:
            print(Fore.RED + f"✗ Login failed: {e}" + Fore.RESET)
            self.kill("login_error")
