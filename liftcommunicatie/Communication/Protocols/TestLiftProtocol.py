from .ICommunicationProtocol import ICommunicationProtocol
import threading
import websocket
import json


class TestLiftProtocol(ICommunicationProtocol):
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.ws_thread = None
        self._connected = threading.Event()
        self._message_callback = None

    
    def connect(self):
        print(f"Attempting to connect to websocket API: {self.url}")
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        self.ws_thread = threading.Thread(target=self._run)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def wait_until_connected(self, timeout=None):
        return self._connected.wait(timeout)

    def is_connected(self):
        return self._connected.is_set()
        

    def setup(self):
        print("Hier komt de logica voor beveiliging, etc...")

    def disconnect(self):
        if self.ws is not None:
            self.ws.close()
        self._connected.clear()

    def send_message(self, message):
        if not self.is_connected():
            raise RuntimeError("Websocket is not connected")

        if not isinstance(message, str):
            message = json.dumps(message)

        self.ws.send(message)

    def _on_open(self, ws):
        print(f"Connected to WS API: {self.url}")
        self._connected.set()

    def set_message_callback(self, callback):
        self._message_callback = callback

    def _on_message(self, ws, message):
        print(f"bericht ontvangen!: {message}")
        if self._message_callback is not None:
            try:
                data = json.loads(message)
                self._message_callback(data)
            except json.JSONDecodeError:
                pass

    def _on_error(self, ws, error):
        self._connected.clear()

    def _on_close(self, ws, close_status_code, close_msg):
        self._connected.clear()

    def _run(self):
        self.ws.run_forever()
    
