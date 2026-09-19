from __future__ import annotations
import threading, webbrowser, time
from .webui.server import run

def main():
    server=run();threading.Thread(target=server.serve_forever,daemon=True).start();url='http://127.0.0.1:8765/'
    try:
        import webview
        webview.create_window('Angel Platform',url,width=1600,height=980,min_size=(1100,700));webview.start()
    except Exception:
        # If the optional pywebview backend is unavailable or fails to start,
        # keep the application usable through the system browser.
        webbrowser.open(url)
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: pass
    finally: server.shutdown()
if __name__=='__main__':main()
