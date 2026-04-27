import platform
import subprocess
import json
import sys
import time

from pathlib import Path
from enum import Enum

from frontend import presentation

class DockerEngineStatus(Enum):
    running = 0
    starting = 1
    stopped = -1
    stopping = -2


def start_mac():
    # Need to call colima to start the docker engine
    subprocess.run(["colima", "start"])

    stall_until_docker_engine_ready()

    if query_docker_engine_status() is not DockerEngineStatus.running:
        error_dialog_script = r'display alert "Could not start" message "Could not start the Docker engine. Please start Docker Desktop manually and try again" as critical buttons {{"OK"}} default button "OK"'
        subprocess.run(["osascript", "-e", error_dialog_script])
        sys.exit(-1)

    start_shared()


def start_windows():

    start_docker_engine_windows()
    start_shared()


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
            print(docker_backend_path.resolve())
            if not docker_backend_path.exists():
                docker_backend_path = None


        except Exception as e:
            print(f"reg query failed, {e}")
            pass # We will fall back to atttempting to open Docker Desktop, might be annoying for the user but oh well
            #ctypes.windll.user32.MessageBoxW(0, "Could not find Docker. Please reinstall NodePipe", "Could not start", 0x10) #0x10 is error icon enum val
            

       #except PermissionError:
       #     ctypes.windll.user32.MessageBoxW(0, "Permission error while attempting to access Docker", "Could not start", 0x10) #0x10 is error icon enum val

    if query_docker_engine_status().value >= DockerEngineStatus.running.value:
        #Docker engine is already running
        return

    # Start the docker engine directly to avoid docker desktop GUI from popping up
    if docker_backend_path is not None:
        print(f"using service to start. path: {str(docker_backend_path)}")
        subprocess.Popen([str(docker_backend_path), "--with-frontend=false"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

    else:
        print("fell back to desktop to start")
        subprocess.Popen(['docker', 'desktop', 'start']) # Fallback to using Docker GUI app to start the Docker engine

    stall_until_docker_engine_ready()

    if query_docker_engine_status() != DockerEngineStatus.running:
        # Timed out while waiting for Docker to start
        ctypes.windll.user32.MessageBoxW(0, "Could not start the Docker engine. Please start Docker Desktop manually and open NodePipe again", "Could not start", 0x10) #0x10 is error icon enum val
        sys.exit(-1)


def start_shared():
    # Start the container
    subprocess.run(["docker", "compose", "up", "-d"])

    # Start the frontend
    presentation.start_app()

def query_docker_engine_status() -> DockerEngineStatus:
    # Check if docker is running already
    docker_status_json = subprocess.run(["docker", "desktop", "status", "--format", "json"], capture_output=True).stdout
    print(f"query returned: {docker_status_json}")
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

def stall_until_docker_engine_ready():
    # Stall until docker is ready
    stall_time = 0
    while query_docker_engine_status() != DockerEngineStatus.running and stall_time < 300:
        time.sleep(1)
        stall_time += 1

if __name__ == "__main__":
    # TODO show splash screen. It could take awhile to spin up the container

    if platform.system() == "Darwin": # Mac
        start_mac()

    else:
        start_windows()
        

    

