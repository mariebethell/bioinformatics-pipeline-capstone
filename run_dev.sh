#!/bin/bash

run_mac() {
	poetry run briefcase run macOS
}

OS="$(uname)"
case $OS in
    'Darwin')
        run_mac
        ;;
    *)
        echo "Unsupported OS"
        ;;
esac