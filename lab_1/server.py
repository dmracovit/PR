import socket
import sys
import os
from pathlib import Path
from urllib.parse import unquote
import mimetypes


class HTTPServer:
    """Simple HTTP file server using TCP sockets"""
    
    def __init__(self, host='0.0.0.0', port=8000, directory='.'):
        self.host = host
        self.port = port
        self.directory = os.path.abspath(directory)
        self.socket = None
        
        mimetypes.init()
        
    def start(self):
        """Start the HTTP server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        print(f"Server running on http://{self.host}:{self.port}")
        print(f"Serving directory: {self.directory}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Accept connection
                client_socket, client_address = self.socket.accept()
                print(f"Connection from {client_address}")
                
                # Handle request
                self.handle_request(client_socket)
                
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            if self.socket:
                self.socket.close()
    
    def handle_request(self, client_socket):
        """Handle a single HTTP request"""
        try:
            # Receive request
            request_data = client_socket.recv(4096).decode('utf-8')
            
            if not request_data:
                client_socket.close()
                return
            
            # Parse request
            print(f"Request:\n{request_data.split(chr(13) + chr(10))[0]}")
            
            request_line = request_data.split('\r\n')[0]
            parts = request_line.split()
            
            if len(parts) < 2:
                self.send_response(client_socket, 400, "Bad Request", b"Bad Request")
                return
            
            method = parts[0]
            path = unquote(parts[1])  # Decode URL encoding
            
            # Only handle GET requests
            if method != 'GET':
                self.send_response(client_socket, 405, "Method Not Allowed", 
                                 b"Method Not Allowed")
                return
            
            # Serve the requested path
            self.serve_path(client_socket, path)
            
        except Exception as e:
            print(f"Error handling request: {e}")
            try:
                self.send_response(client_socket, 500, "Internal Server Error", 
                                 b"Internal Server Error")
            except:
                pass
        finally:
            client_socket.close()
    
    def serve_path(self, client_socket, url_path):
        """Serve a file or directory"""
        # Remove leading slash and construct file path
        if url_path == '/':
            file_path = self.directory
        else:
            file_path = os.path.join(self.directory, url_path.lstrip('/'))
        
        # Normalize path to prevent directory traversal attacks
        file_path = os.path.abspath(file_path)
        
        # Security check: ensure path is within served directory
        if not file_path.startswith(self.directory):
            self.send_response(client_socket, 403, "Forbidden", b"Forbidden")
            return
        
        # Check if path exists
        if not os.path.exists(file_path):
            self.send_response(client_socket, 404, "Not Found", 
                             b"<h1>404 Not Found</h1>", "text/html")
            return
        
        # If it's a directory, generate directory listing
        if os.path.isdir(file_path):
            self.serve_directory(client_socket, file_path, url_path)
        else:
            self.serve_file(client_socket, file_path)
    
    def serve_file(self, client_socket, file_path):
        """Serve a single file"""
        try:
            # Determine content type
            content_type = self.get_content_type(file_path)
            
            # Check if content type is supported
            if content_type == "application/octet-stream":
                ext = os.path.splitext(file_path)[1]
                if ext not in ['.html', '.htm', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.css', '.js', '.txt']:
                    print(f"Unsupported file type: {ext}")
                    self.send_response(client_socket, 415, "Unsupported Media Type",
                                     b"<h1>415 Unsupported Media Type</h1>", "text/html")
                    return
            
            # Read file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            print(f"Serving file: {file_path} ({len(content)} bytes)")
            self.send_response(client_socket, 200, "OK", content, content_type)
            
        except Exception as e:
            print(f"Error serving file: {e}")
            self.send_response(client_socket, 500, "Internal Server Error",
                             b"Internal Server Error")
    
    def serve_directory(self, client_socket, dir_path, url_path):
        """Generate and serve directory listing"""
        try:
            # Ensure url_path ends with /
            if not url_path.endswith('/'):
                url_path += '/'
            
            # Get directory contents
            items = os.listdir(dir_path)
            items.sort()
            
            # Generate HTML
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Directory listing for {url_path}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .folder {{ font-weight: bold; }}
        .folder:before {{ content: "📁 "; }}
        .file:before {{ content: "📄 "; }}
    </style>
</head>
<body>
    <h1>Directory listing for {url_path}</h1>
    <hr>
    <ul>
"""
            
            # Add parent directory link if not root
            if url_path != '/':
                parent_path = '/'.join(url_path.rstrip('/').split('/')[:-1])
                if not parent_path:
                    parent_path = '/'
                html += f'        <li><a href="{parent_path}" class="folder">Parent Directory</a></li>\n'
            
            # Add items
            for item in items:
                item_path = os.path.join(dir_path, item)
                item_url = url_path + item
                
                if os.path.isdir(item_path):
                    html += f'        <li><a href="{item_url}/" class="folder">{item}/</a></li>\n'
                else:
                    html += f'        <li><a href="{item_url}" class="file">{item}</a></li>\n'
            
            html += """    </ul>
    <hr>
</body>
</html>"""
            
            print(f"Serving directory listing: {dir_path}")
            self.send_response(client_socket, 200, "OK", html.encode('utf-8'), "text/html")
            
        except Exception as e:
            print(f"Error serving directory: {e}")
            self.send_response(client_socket, 500, "Internal Server Error",
                             b"Internal Server Error")
    
    def get_content_type(self, file_path):
        """Determine MIME type for a file"""
        # Get extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Map common extensions
        content_types = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.txt': 'text/plain',
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def send_response(self, client_socket, status_code, status_text, body, 
                     content_type='text/html'):
        """Send HTTP response"""
        # Ensure body is bytes
        if isinstance(body, str):
            body = body.encode('utf-8')
        
        # Construct response
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(body)}\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"
        
        # Send response
        client_socket.sendall(response.encode('utf-8') + body)
        print(f"Response: {status_code} {status_text}\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python server.py <directory> [port]")
        print("Example: python server.py ./www 8000")
        sys.exit(1)
    
    directory = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    server = HTTPServer(host='0.0.0.0', port=port, directory=directory)
    server.start()


if __name__ == '__main__':
    main()
