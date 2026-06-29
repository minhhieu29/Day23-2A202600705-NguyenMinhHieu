from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8'))
        
        # Log to console
        print(f"\n--- Webhook received at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        print(json.dumps(payload, indent=2))
        
        # Log to file
        with open('submission/webhook-events.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- Webhook received at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(json.dumps(payload, indent=2) + "\n")
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

def run(server_class=HTTPServer, handler_class=WebhookHandler, port=9099):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting mock Slack webhook server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Stopping mock Slack webhook server.")

if __name__ == '__main__':
    run()
