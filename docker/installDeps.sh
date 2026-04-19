export PATH="$PATH:/root/.local/bin"
alias python='python3.11' python3='python3.11'

ls -all .
. ./venv/bin/activate
pipx install poetry
poetry install