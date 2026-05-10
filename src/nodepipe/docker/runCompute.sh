export PATH="$PATH:/root/.local/bin"
#alias python='python3.11' python3='python3.11'

bash dockerd-entrypoint.sh --storage-driver=vfs &
sleep 5 # Let the Docker daemon come up

. ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:. 
python3 ./network/server/manage.py runserver 0.0.0.0:8000