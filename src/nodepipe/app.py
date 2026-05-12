import platform
import subprocess
import json
import sys
import time
import shutil
import asyncio
import ipaddress
import aiohttp
import os

from pathlib import Path
from enum import Enum
from importlib import resources
from PySide6 import QtWidgets, QtGui, QtCore

from frontend import presentation

from network.client.NetClient import NetClient

class DockerEngineStatus(Enum):
    running = 0
    starting = 1
    stopped = -1
    stopping = -2

class App:
    mac_paths = ["usr/local/bin", "/opt/homebrew/bin", "/usr/bin"]
    mac_pathvar = os.pathsep.join(mac_paths + os.environ.get("PATH", "").split(os.pathsep))

    @staticmethod
    def start_mac(qt_app: QtWidgets.QApplication, splash_screen: QtWidgets.QSplashScreen):
        # Need to call colima to start the docker engine
        App._upd_splash_msg(splash_screen, "Starting Docker engine...")

        cur_env = os.environ.copy()
        cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
        subprocess.run(["colima", "start"], env=cur_env)
        App._upd_splash_msg(splash_screen, "Waiting for Docker engine to initialize...")

        App.stall_until_docker_engine_ready()

        if App.query_docker_engine_status() is not DockerEngineStatus.running:
            error_dialog_script = r'display alert "Could not start" message "Could not start the Docker engine. Please start Docker Desktop manually and try again" as critical buttons {{"OK"}} default button "OK"'
            subprocess.run(["osascript", "-e", error_dialog_script], env=cur_env)
            sys.exit(-1)

        App._upd_splash_msg(splash_screen, "Docker engine started")

        App.start_shared(qt_app, splash_screen)


    @staticmethod
    def start_windows(qt_app: QtWidgets.QApplication, splash_screen: QtWidgets.QSplashScreen):

        App.start_docker_engine_windows(splash_screen)
        App.start_shared(qt_app, splash_screen)


    @staticmethod
    def start_docker_engine_windows(splash_screen: QtWidgets.QSplashScreen):
        import winreg # Import is here to prevent loading on other OS
        import ctypes # For windows error box

        print("Starting Docker...")
        App._upd_splash_msg(splash_screen, "Starting Docker engine...")

        # Pull docker service path from registry
        docker_backend_path = None
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\com.docker.service", 0, winreg.KEY_READ) as service_key:
            try:
                docker_service_path, _ = winreg.QueryValueEx(service_key, "ImagePath")
                docker_service_path = docker_service_path.replace('"', '') # String literally has quotes in it, get rid of them

                # Service path isn't actually what we need, but it's convenient to get there
                docker_backend_path = Path(docker_service_path).resolve().parent / "resources" / "com.docker.backend.exe"
                if not docker_backend_path.exists():
                    docker_backend_path = None


            except Exception as e:
                pass # We will fall back to atttempting to open Docker Desktop, might be annoying for the user but oh well
                #ctypes.windll.user32.MessageBoxW(0, "Could not find Docker. Please reinstall NodePipe", "Could not start", 0x10) #0x10 is error icon enum val
                

           #except PermissionError:
           #     ctypes.windll.user32.MessageBoxW(0, "Permission error while attempting to access Docker", "Could not start", 0x10) #0x10 is error icon enum val

        if App.query_docker_engine_status().value >= DockerEngineStatus.running.value:
            #Docker engine is already running
            App._upd_splash_msg(splash_screen, "Docker engine running")
            return

        # Start the docker engine directly to avoid docker desktop GUI from popping up
        try:
            if docker_backend_path is None:
                raise ValueError()
            
            subprocess.Popen(['powershell', '-Command', f"Start-Process -FilePath '{str(docker_backend_path)}' -ArgumentList '-unattended' -WindowStyle Hidden"])

        except (ValueError, OSError):
            App._upd_splash_msg(splash_screen, "Failed to silently start Docker. Launching full Docker Desktop...")
            subprocess.Popen(['docker', 'desktop', 'start']) # Fallback to using Docker GUI app to start the Docker engine

        print("Waiting for Docker to finish initializing...")
        App._upd_splash_msg(splash_screen, "Waiting for Docker engine to initialize...")

        App.stall_until_docker_engine_ready()

        if App.query_docker_engine_status() != DockerEngineStatus.running:
            # Timed out while waiting for Docker to start
            ctypes.windll.user32.MessageBoxW(0, "Could not start the Docker engine. Please start Docker Desktop manually and open NodePipe again", "Could not start", 0x10) #0x10 is error icon enum val
            sys.exit(-1)
            
        print("Docker started!")
        App._upd_splash_msg(splash_screen, "Docker engine started")


    @staticmethod
    def start_shared(qt_app: QtWidgets.QApplication, splash_screen: QtWidgets.QSplashScreen):
        # Start the container
        print("Launching compute container...")
        App._upd_splash_msg(splash_screen, "Building compute container (this may take a few minutes)...")

        cd = Path(__file__).resolve().parent
        cur_env = os.environ.copy()
        cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
        subprocess.run(["docker", "compose", "up", "-d"], cwd=str(cd), env=cur_env)
        
        # Stall until the compute server is listening
        print("Waiting for container to finish initializing...")
        App._upd_splash_msg(splash_screen, "Waiting for compute container to initialize...")

        App.stall_until_compute_server_ready()

        print("Container ready!")
        App._upd_splash_msg(splash_screen, "Compute container ready. Starting NodePipe...")

        # Drop loading splash, we're done loading
        splash_screen.close()

        # Start the frontend
        presentation.start_app(qt_app)

    @staticmethod
    def query_docker_engine_status() -> DockerEngineStatus:
        # Check if docker is running already
        if platform.system() == "Darwin": # Mac
            return App.query_docker_engine_status_mac()

        else:
            return App.query_docker_engine_status_windows()


    @staticmethod
    def query_docker_engine_status_windows() -> DockerEngineStatus:
        docker_status_json = subprocess.run(["docker", "desktop", "status", "--format", "json"], capture_output=True).stdout
        docker_status = 'stopped' # Assume stopped by default

        try:
            docker_status_dict = json.loads(docker_status_json)
            docker_status = docker_status_dict['Status']

        except (json.JSONDecodeError, TypeError):
            # Docker returns plain text even when asking for json if engine is not running. Assume it's off
            pass

        status_enum = DockerEngineStatus.stopped
        try:
            status_enum = DockerEngineStatus[docker_status]
        
        except (ValueError, KeyError):
            pass # Assume stopped

        return status_enum

    @staticmethod
    def query_docker_engine_status_mac():
        cur_env = os.environ.copy()
        cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
        colima_status_json = subprocess.run(['colima', 'status', '--json'], capture_output=True, env=cur_env).stdout

        try:
            json.loads(colima_status_json)
            return DockerEngineStatus.running # Colima has no status field. It either returns valid JSON if running or it doesnt

        except (json.JSONDecodeError, TypeError) as e:
            print(f"caught {e}")
            pass # Colima must not be running or is still starting

        return DockerEngineStatus.stopped

    @staticmethod
    def stall_until_docker_engine_ready():
        # Stall until docker is ready
        stall_time = 0
        while App.query_docker_engine_status() != DockerEngineStatus.running and stall_time < 300:
            time.sleep(1)
            stall_time += 1
            
    @staticmethod
    def stall_until_compute_server_ready():
        stall_time = 0
        saw_ping = False
        while not saw_ping and stall_time < 30:
            try:
                pingTime = asyncio.run(NetClient._ping_server(ipaddress.ip_address("127.0.0.1"), 8000))
                if pingTime is not None:
                    saw_ping = True
            
            except (aiohttp.client_exceptions.ServerDisconnectedError, aiohttp.ClientConnectorError, asyncio.TimeoutError):
                pass # Server isn't ready to accept a connection yet
                
            time.sleep(1)
            stall_time += 1
            
        return

    @staticmethod
    def ensure_docker_windows(splash_screen: QtWidgets.QSplashScreen):
        App._upd_splash_msg(splash_screen, "Checking if Docker is installed...")

        if shutil.which("docker"):
            App._upd_splash_msg(splash_screen, "Docker is installed")
            return # Docker is already installed
            
        # Need to install docker

        App._upd_splash_msg(splash_screen, "Docker not found. Launching installer")

        import ctypes # For windows message box TODO switch to using Qt dialog
        with resources.path("nodepipe.resources", "Docker Desktop Installer.exe") as installer_path:
            subprocess.run([str(installer_path), "install", "--quiet", "--accept-license"], check=True)
            ctypes.windll.user32.MessageBoxW(0, "Docker installation complete. Please reboot your computer before running NodePipe again.", "Please reboot your device", 0x30) #0x30 is warning icon enum val
            sys.exit(0)

        # If we get here, install failed somehow? Maybe installer wasn't packaged
        ctypes.windll.user32.MessageBoxW(0, "Failed to install Docker. Please try again or install Docker Desktop manually", "Installation Error", 0x30) #0x30 is warning icon enum val
        sys.exit(-1)

    @staticmethod
    def ensure_docker_mac(splash_screen: QtWidgets.QSplashScreen):
        App.ensure_brew_mac(splash_screen)
        App.ensure_colima_mac(splash_screen)
        
        App._upd_splash_msg(splash_screen, "Checking if Docker is installed...")

        if shutil.which("docker", path=App.mac_pathvar) is None:
            # Need to install docker

            App._upd_splash_msg(splash_screen, "Docker not found. Installing...")

            cur_env = os.environ.copy()
            cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']

            subprocess.run(['brew', 'install', '--quiet', 'docker'], env=cur_env)

        App._upd_splash_msg(splash_screen, "Docker installed")

        return
        
    @staticmethod
    def ensure_brew_mac(splash_screen: QtWidgets.QSplashScreen):
        App._upd_splash_msg(splash_screen, "Checking if Homebrew is installed...")

        if shutil.which("brew", path=App.mac_pathvar) is None:
            # Need to install brew

            App._upd_splash_msg(splash_screen, "Homebrew not found. Installing...")

            pass_helper_path = Path(__file__).resolve().parent / 'mac_askpass.sh'
            os.chmod(pass_helper_path, 0o744)

            cur_env = os.environ.copy()
            cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
            
            App._upd_splash_msg(splash_screen, "Installing XCode-Select...")

            subprocess.run(['xcode-select', '--install'], env=cur_env)
            App.stall_until_xcode_ready()

            App._upd_splash_msg(splash_screen, "Resuming Homebrew installation...")

            auto_env = os.environ.copy()
            auto_env['NONINTERACTIVE'] = '1'
            auto_env['SUDO_ASKPASS'] = str(pass_helper_path)
            auto_env['PATH'] = App.mac_pathvar + os.pathsep + auto_env['PATH']
            subprocess.run('sudo -A echo "Elevated"; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', shell=True, env=auto_env)

        App._upd_splash_msg(splash_screen, "Homebrew installed")
            
        return

    @staticmethod
    def stall_until_xcode_ready():
        # Stall until xcode CLI tools is installed
        stall_time = 0
        while not App.query_xcode_ready() and stall_time < 300:
            time.sleep(1)
            stall_time += 1

        if stall_time > 5 and App.query_xcode_ready():
            time.sleep(10) # Give xcode time to finalize install

    @staticmethod
    def query_xcode_ready():
        cur_env = os.environ.copy()
        cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
        xcode_status = subprocess.run(['xcode-select', '-p'], capture_output=True, text=True, env=cur_env).stdout
        #print(f"type: {type(xcode_status)} {xcode_status}")

        if xcode_status is None:
            #print("xcode not ready, returned none")
            return False
        
        elif len(xcode_status) == 0:
            #print("xcode is not ready, returned empty str")
            return False
        
        elif xcode_status.startswith("xcode-select: error: Unable to get active developer directory"):
            # xcode is not installed yet
            #print("xcode not ready")
            return False
        
        elif xcode_status.startswith(r"/Library/"):
            # xcode is installed
            #print("xcode already installed")
            return True

        raise ValueError(f"Unexpected result from xcode: {xcode_status}")
        return False

        
    @staticmethod
    def ensure_colima_mac(splash_screen: QtWidgets.QSplashScreen):
        App._upd_splash_msg(splash_screen, "Checking if Colima is installed...")

        if shutil.which("colima", path=App.mac_pathvar) is None:
            # Need to install colima

            App._upd_splash_msg(splash_screen, "Colima not found. Installing...")

            cur_env = os.environ.copy()
            cur_env['PATH'] = App.mac_pathvar + os.pathsep + cur_env['PATH']
            subprocess.run(['brew', 'install', '--quiet', 'colima'], env=cur_env)

        App._upd_splash_msg(splash_screen, "Colima installed")
        
        return
    
    @staticmethod
    def create_venv(splash_screen: QtWidgets.QSplashScreen):
        App._upd_splash_msg(splash_screen, "Setting up environment...")

        shared_path = Path(__file__).resolve().parent / "shared-data"
        shared_path.mkdir(parents=False, exist_ok=True)

        env_path = Path(__file__).resolve().parent / ".env"
        if not env_path.exists():
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_data = f"SHARED_DATA_PATH='{shared_path}'"
                env_file.write(env_data)

        App._upd_splash_msg(splash_screen, "Environment setup completed")

    @staticmethod
    def _upd_splash_msg(splash_screen: QtWidgets.QSplashScreen, msg: str):
        splash_screen.showMessage(f"{msg}\n", 
                                  QtCore.Qt.AlignmentFlag.AlignBottom \
                                  | QtCore.Qt.AlignmentFlag.AlignCenter, 
                                  QtCore.Qt.GlobalColor.white)

    @staticmethod
    def bootup():
        # Show splash screen. It could take awhile to spin up the container
        qt_app = QtWidgets.QApplication([])

        splash_bitmap = QtGui.QPixmap("./resources/img/splash.png")
        splash_screen = QtWidgets.QSplashScreen(splash_bitmap, QtCore.Qt.WindowType.WindowStaysOnTopHint)
        splash_screen.show()
        qt_app.processEvents()

        App.create_venv(splash_screen)

        if platform.system() == "Darwin": # Mac
            print("Mac OS Detected")
            App.ensure_docker_mac(splash_screen)
            App.start_mac(qt_app, splash_screen)

        else:
            App.ensure_docker_windows(splash_screen)
            App.start_windows(qt_app, splash_screen)


if __name__ == "__main__":
    App.bootup()