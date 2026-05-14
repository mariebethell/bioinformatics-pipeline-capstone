from PySide6 import QtWebEngineWidgets, QtCore
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtCore import QObject, Signal, QThread, QCoreApplication, QPoint, QEvent, Qt, QTimer
from PySide6.QtGui import QMouseEvent

from queue import Queue

from pathlib import Path


class WebView(QtWebEngineWidgets.QWebEngineView):
    class DispatchWorker(QObject):
        upload_signal = Signal(Path)

        def __init__(self, queue):
            super().__init__()
            self.queue = queue

        def run(self):
            print("Started OneDrive dispatch worker")
            while True:
                try:
                    uri = self.queue.get(block=True, timeout=None)
                    self.upload_signal.emit(uri)
                    
                except Exception as e:
                    print(f"WARNING: Unhandled exception in OneDrive dispatch worker. Ignoring. Exception: {e}")

    dispatcher_start_signal = Signal()

    def __init__(self, folder_url: str = 'https://csusm-my.sharepoint.com/:f:/g/personal/lopez2349_csusm_edu/IgA49nG5FJ9zQKUU0pp3-bzpAai6HcPCUIlidkIByGlnaKE?e=kgOb2v'):
        super().__init__()

        self.setPage(self.UploadablePage(self))

        self._uris_to_upload = Queue() # Queue of Paths
        self._staged_file = None

        self.dispatch_worker = None
        self.dispatch_worker_thread = None
        
        # allows for external windows to be opened
        self.settings().setAttribute(self.settings().WebAttribute.JavascriptCanOpenWindows, True)

        self.page().chooseFiles
        self.setUrl(QtCore.QUrl(folder_url))
        self.loadFinished.connect(self._handle_page_loaded)


    def _handle_page_loaded(self, success):
        if success:
            self._start_dispatch_worker()

        else:
            print("ERROR: Webview page failed to load. Aborting OneDrive handler init")
            return

    def _start_dispatch_worker(self):
        print("Starting OneDrive dispatch worker")
        if self.dispatch_worker is not None:
            print("ERROR: Attempted to start OneDrive dispatcher when one already exists. Ignoring...")
            return

        
        self.dispatch_worker = self.DispatchWorker(self._uris_to_upload)
        self.dispatch_worker_thread = QThread()
        self.dispatch_worker.moveToThread(self.dispatch_worker_thread)
        self.dispatcher_start_signal.connect(self.dispatch_worker.run)
        self.dispatch_worker.upload_signal.connect(self._upload_file)
        self.dispatch_worker_thread.start()
        self.dispatcher_start_signal.emit()

    def _upload_file(self, uri: Path):

        if uri is None:
            print("WARNING: Given null URI for file to upload to OneDrive")
            return

        if type(uri) is str:
            try:
                uri = Path(uri)

            except TypeError:
                print(f"WARNING: OneDrive dispatcher given type which cannot be coerced into a Path: {type(uri)}. Ignoring...")
                return
            
            except Exception as e:
                print("WARNING: OneDrive dispatcher failed to parse given Path. Ignoring. Exception: {e}")
                return

        if not isinstance(uri, Path):
            print(f"WARNING: OneDrive dispatcher given illegal type for URI: {type(uri)}. Ignoring...")
            return
        
        try:
            uri = uri.resolve()

        except RuntimeError:
            print("WARNING: OneDrive dispatcher failed to resolve the given Path. Ignoring...")
            return
        
        except Exception:
            print("WARNING: OneDrive dispatcher failed to resolve the given path due to an exception. Ignoring. Exception: {e}")


        if self._staged_file is not None:
            raise RuntimeError("ERROR: OneDrive dispatcher attempted to stage a file but one was already staged!")
        
        self._staged_file = uri

        try:
            injector = f"""
                (function() {{
                    try
                    {{
                        let input = document.getElementById('input-injector');

                        if (!input) {{
                            input = document.createElement('input');
                            input.type = 'file';
                            input.id = 'input-injector';
                            input.style.display = 'inline';
                            input.style.position = 'fixed';
                            input.style.top = '0';
                            input.style.left = '0';
                            input.style.width = '10px';
                            input.style.height = '10px';
                            input.style.opacity = '0.01';
                            input.style.zIndex = '999999';
                            document.body.appendChild(input);
                        }}

                        if ({str(uri.is_dir()).lower()})
                        {{
                            input.setAttribute('webkitdirectory', '');
                            input.setAttribute('directory', '');
                        }}
                        else
                        {{
                            input.removeAttribute('webkitdirectory');
                            input.removeAttribute('directory');
                        }}
                    }}
                    catch (err)
                    {{
                        console.error("Failed to inject input div: ", err.message);
                    }}
                }})();
                """
            self.page().runJavaScript(injector, self._simulate_click)

        except Exception as e:
            print(f"ERROR: OneDrive dispatcher ran into an exception while attempting to inject file div: {e}")
            return

    def _simulate_click(self, result):
        target = self.focusProxy()
        pos = QPoint(5, 5)

        press = QMouseEvent(QEvent.MouseButtonPress, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        release = QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

        QCoreApplication.postEvent(target, press)
        QCoreApplication.postEvent(target, release)

        QTimer.singleShot(100, self._simulate_drag_drop)
    
    def _simulate_drag_drop(self):
        try:
            drop_script = """
            (function() {
                try
                {
                    const tempInput = document.getElementById('input-injector');
                    const dropZone = document.querySelector('[role="main"]');
                    
                    if (tempInput && tempInput.files.length > 0 && dropZone)
                    {
                        const dataTransfer = new DataTransfer();
                        for (let i = 0; i < tempInput.files.length; i++)
                        {
                            dataTransfer.items.add(tempInput.files[i]);
                        }

                        const events = ['dragenter', 'dragover', 'drop'];
                        events.forEach(name => {
                            const event = new DragEvent(name, {
                                bubbles: true,
                                cancelable: true,
                                dataTransfer: dataTransfer
                            });
                            dropZone.dispatchEvent(event);
                        });

                        tempInput.remove();
                    }
                }
                catch (err)
                {
                    console.error("Failed to simulate drag and drop event: ", err.message);
                }
            })();
            """
            self.page().runJavaScript(drop_script)

        except Exception as e:
            print(f"ERROR: OneDrive drag and drop failed due to exception {e}")
    
    class UploadablePage(QWebEnginePage):
        def __init__(self, parent):
            super().__init__(parent)
            self.web_view = parent

        def javaScriptConsoleMessage(self, level, message, line, sourceID):
            return
            #print(f"JS: {message} (line {line})")

        def chooseFiles(self, mode, old_files, accepted_mimetypes): # Override
            staged = [self.web_view._staged_file.as_posix()] if self.web_view._staged_file else []
            self.web_view._staged_file = None
            return staged

    
    def upload_file(self, path: Path):
        if not isinstance(path, Path) and type(path) is not str:
            raise ValueError("Invalid path type")
        
        if type(path) is str:
            try:
                path = Path(path)

            except TypeError:
                raise ValueError("Input path was invalid")
        
            except Exception as e:
                raise ValueError(f"Input path caused exception: {e}")
            
        try:
            path = path.resolve()
           
        except RuntimeError:
            raise ValueError("Input path could not be resolved")
        
        except Exception as e:
            raise ValueError(f"Input path caused exception: {e}")
        
        self._uris_to_upload.put(path)