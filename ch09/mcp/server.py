from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys

class SimpleMCPMock(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))
        
        method = body.get("method")
        req_id = body.get("id")
        response = {"jsonrpc": "2.0", "id": req_id}
        
        # 1. Handle Tools Listing
        if method == "tools/list":
            response["result"] = {
                "tools": [{
                    "name": "get_fence_status",
                    "description": "Get the current voltage and power status for a specific pasture fence zone.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "zone_name": {"type": "string"}
                        },
                        "required": ["zone_name"]
                    }
                }]
            }
        
        # 2. Handle Tool Execution
        elif method == "tools/call":
            params = body.get("params", {})
            arguments = params.get("arguments", {})
            zone = arguments.get("zone_name", "Unknown Pasture")
            
            response["result"] = {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "zone": zone,
                        "status": "OFF",
                        "voltage_kv": 0.0,
                        "alert": "Cattle at risk of escaping"
                    })
                }]
            }
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}
            
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == "__main__":
    print("Mock MCP Server running on port 8000...", flush=True)
    try:
        HTTPServer(('0.0.0.0', 8000), SimpleMCPMock).serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.", flush=True)
        sys.exit(0)
