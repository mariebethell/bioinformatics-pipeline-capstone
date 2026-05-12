run_mac() {
    rm -rf ./build

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
