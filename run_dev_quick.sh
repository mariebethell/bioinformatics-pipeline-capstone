run_mac() {
    bash -c 'cd ./src/nodepipe; python3 app.py'
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
