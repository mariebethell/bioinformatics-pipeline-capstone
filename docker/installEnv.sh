export PATH="$PATH:/root/.local/bin"

dnf install -y python3.11
alias python='python3.11' python3='python3.11'
mkdir venv
python3 -m venv ./venv
. ./venv/bin/activate
python3 -m ensurepip --upgrade
pip install pipx