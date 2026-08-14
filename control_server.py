from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import os

PORT = 8765
PROCESS = None

class Handler(BaseHTTPRequestHandler):

    def send_json(self, code, text):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):

        global PROCESS

        if self.path == "/start":

            if PROCESS is None or PROCESS.poll() is not None:

                PROCESS = subprocess.Popen([
                    "python",
                    os.path.expanduser(
                        "~/myassistant_V3/voice_bridge.py"
                    )
                ])

            self.send_json(200, '{"running":true}')
            return

        if self.path == "/stop":

            if PROCESS and PROCESS.poll() is None:
                PROCESS.terminate()

            PROCESS = None

            self.send_json(200, '{"running":false}')
            return

        if self.path == "/status":

            running = (
                PROCESS is not None
                and PROCESS.poll() is None
            )

            self.send_json(
                200,
                '{"running":' + str(running).lower() + '}'
            )
            return

        self.send_json(404, '{"error":"not found"}')


server = HTTPServer(("127.0.0.1", PORT), Handler)

print("MyAssistant control server:", PORT)

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
