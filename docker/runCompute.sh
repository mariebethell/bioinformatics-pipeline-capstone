export PATH="$PATH:/root/.local/bin"
alias python='python3.11' python3='python3.11'

. ./venv/bin/activate
python3 ./network/manage.py runserver 0.0.0.0:8000