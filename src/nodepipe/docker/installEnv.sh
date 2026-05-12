export PATH="$PATH:/root/.local/bin"

apk update
#apk add gcompat
apk add bash
apk add curl
apk add openjdk21
apk add python3=3.11.14-r0 --repository=http://dl-cdn.alpinelinux.org/alpine/v3.19/main
#apk add python3-dev=3.11.14-r0 --repository=http://dl-cdn.alpinelinux.org/alpine/v3.19/main
#apk add build-base
#apk add libffi-dev
#apk add openssl-dev

#dnf install -y python3.11
#alias python='python3.11' python3='python3.11'
mkdir venv
python3 -m venv ./venv
. ./venv/bin/activate
python3 -m ensurepip --upgrade
pip install --upgrade pip setuptools wheel
pip install pipx

curl -s https://get.nextflow.io | bash
chmod +x nextflow
mv nextflow /usr/local/bin/nextflow