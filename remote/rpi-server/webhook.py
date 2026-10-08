import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/trigger-script':
            try:
                result = subprocess.run(
                    ['/home/siddarth/Documents/rpi-server/mapping/docker-restart.sh'],
                    capture_output=True,
                    text=True,
                    check=False # make check as true and properly handle it as it helps exit the code quicker and also finds hidden errors and helps make sure that the script does not fail silently
                )
                
                if result.returncode == 0:
                    self.send_response(200)
                    self.end_headers()
                    success_msg=f"Success :{result.stdout}"
                    self.wfile.write(success_msg.encode('utf-8'))
                else:
                    # 500 Internal Server Error is standard for a failed backend process
                    self.send_response(500) 
                    self.end_headers()
                    error_msg = f"Failed with exit code {result.returncode}\nError Log:\n{result.stdout}\n{result.stderr}"
                    self.wfile.write(error_msg.encode('utf-8'))              
                    
            except Exception as e:  # noqa: BLE001
                # Catch cases where the script file doesn't exist or isn't executable
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Failed to execute script: {str(e)}\n".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

# Listen on port 8080
print("Listening on port 8080...")
HTTPServer(('0.0.0.0', 8080), WebhookHandler).serve_forever()