from PySide6 import QtWebEngineWidgets, QtCore

class WebView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self):
        super().__init__()
        
        # allows for external windows to be opened
        self.settings().setAttribute(self.settings().WebAttribute.JavascriptCanOpenWindows, True)

        self.setUrl(QtCore.QUrl('https://login.microsoftonline.com/common/oauth2/v2.0/authorize'))
