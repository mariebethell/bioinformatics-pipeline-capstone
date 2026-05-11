build_mac() {
	rm -rf ./build
	rm -rf ./dist

	poetry run briefcase create macOS
	poetry run briefcase build macOS
	poetry run briefcase package macOS
}

OS="$(uname)"
case $OS in
    'Darwin')
        build_mac
        ;;
    *)
        echo "Unsupported OS"
        ;;
esac
