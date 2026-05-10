export PATH="$PATH:/root/.local/bin"
#alias python='python3.11' python3='python3.11'

. ./venv/bin/activate
pipx install poetry
poetry install --without dev,ui