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

from frontend import presentation

from network.client.NetClient import NetClient

class DockerEngineStatus(Enum):
    running = 0
    starting = 1
    stopped = -1
    stopping = -2

class App:
    @staticmethod
    def start_mac():
        # Need to call colima to start the docker engine
        subprocess.run(["colima", "start"])

        App.stall_until_docker_engine_ready()

        if App.query_docker_engine_status() is not DockerEngineStatus.running:
            error_dialog_script = r'display alert "Could not start" message "Could not start the Docker engine. Please start Docker Desktop manually and try again" as critical buttons {{"OK"}} default button "OK"'
            subprocess.run(["osascript", "-e", error_dialog_script])
            sys.exit(-1)

        App.start_shared()


    @staticmethod
    def start_windows():

        App.start_docker_engine_windows()
        App.start_shared()


    @staticmethod
    def start_docker_engine_windows():
        import winreg # Import is here to prevent loading on other OS
        import ctypes # For windows error box

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
            return

        # Start the docker engine directly to avoid docker desktop GUI from popping up
        if docker_backend_path is not None:
            subprocess.Popen([str(docker_backend_path), "--with-frontend=false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

        else:
            subprocess.Popen(['docker', 'desktop', 'start']) # Fallback to using Docker GUI app to start the Docker engine

        App.stall_until_docker_engine_ready()

        if App.query_docker_engine_status() != DockerEngineStatus.running:
            # Timed out while waiting for Docker to start
            ctypes.windll.user32.MessageBoxW(0, "Could not start the Docker engine. Please start Docker Desktop manually and open NodePipe again", "Could not start", 0x10) #0x10 is error icon enum val
            sys.exit(-1)


    @staticmethod
    def start_shared():
        # Start the container
        cd = Path(__file__).resolve().parent
        subprocess.run(["docker", "compose", "up", "-d"], cwd=str(cd))
        
        # Stall until the compute server is listening
        App.stall_until_compute_server_ready()

        # Start the frontend
        presentation.start_app()

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
        colima_status_json = subprocess.run(['colima', 'status', '--json'], capture_output=True).stdout

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
    def ensure_docker_windows():
        if shutil.which("docker"):
            return # Docker is already installed
            
        # Need to install docker
        import ctypes # For windows message box
        with resources.path("nodepipe.resources", "Docker Desktop Installer.exe") as installer_path:
            subprocess.run([str(installer_path), "install", "--quiet", "--accept-license"], check=True)
            ctypes.windll.user32.MessageBoxW(0, "Docker installation complete. Please reboot your computer before running NodePipe again.", "Please reboot your device", 0x30) #0x30 is warning icon enum val
            sys.exit(0)

    @staticmethod
    def ensure_docker_mac():
        App.ensure_brew_mac()
        App.ensure_colima_mac()
        
        if shutil.which("docker") is None:
            # Need to install docker
            subprocess.run(['brew', 'install', '--quiet', 'docker'])
        
    @staticmethod
    def ensure_brew_mac():
        if shutil.which("brew") is None:
            # Need to install brew
            pass_helper_path = Path(__file__).resolve().parent / 'mac_askpass.sh'
            os.chmod(pass_helper_path, 0o744)
            
            subprocess.run(['xcode-select', '--install'])

            auto_env = os.environ.copy()
            auto_env['NONINTERACTIVE'] = '1'
            auto_env['SUDO_ASKPASS'] = str(pass_helper_path)
            subprocess.run('sudo -A echo "Elevated"; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', shell=True, env=auto_env)
            
        return
        
    @staticmethod
    def ensure_colima_mac():
        if shutil.which("colima") is None:
            # Need to install colima
            subprocess.run(['brew', 'install', '--quiet', 'colima'])
        
        return
    
    @staticmethod
    def create_venv():
        shared_path = Path(__file__).resolve().parent / "shared-data"
        shared_path.mkdir(parents=False, exist_ok=True)

        env_path = Path(__file__).resolve().parent / ".env"
        if not env_path.exists():
            with open(env_path, "w", encoding="utf-8") as env_file:
                env_data = f"SHARED_DATA_PATH='{shared_path}'"
                env_file.write(env_data)

    @staticmethod
    def bootup():
        # TODO show splash screen. It could take awhile to spin up the container

        App.create_venv()

        if platform.system() == "Darwin": # Mac
            print("Mac OS Detected")
            App.ensure_docker_mac()
            App.start_mac()

        else:
            App.ensure_docker_windows()
            App.start_windows()

if __name__ == "__main__":
    App.bootup()

