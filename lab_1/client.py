import socket
import sys
import os
from urllib.parse import urlparse


class HTTPClient:
    """Simple HTTP client using TCP sockets"""
    
    def __init__(self):
        self.socket = None
    
    def request(self, host, port, path, save_dir):
        """Send HTTP GET request and handle response"""
        try:
            # Create TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to server
            print(f"Connecting to {host}:{port}...")
            self.socket.connect((host, port))
            
            # Construct HTTP GET request
            request = f"GET {path} HTTP/1.1\r\n"
            request += f"Host: {host}:{port}\r\n"
            request += "Connection: close\r\n"
            request += "\r\n"
            
            # Send request
            print(f"Sending request for: {path}")
            self.socket.sendall(request.encode('utf-8'))
            
            # Receive response
            response_data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # Parse response
            self.parse_response(response_data, save_dir)
            
        except ConnectionRefusedError:
            print(f"Error: Could not connect to {host}:{port}")
            print("Make sure the server is running.")
            sys.exit(1)
        except socket.gaierror:
            print(f"Error: Could not resolve host '{host}'")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            if self.socket:
                self.socket.close()
    
    def parse_response(self, response_data, save_dir):
        """Parse HTTP response and handle based on content type"""
        try:
            # Split headers and body
            header_end = response_data.find(b"\r\n\r\n")
            if header_end == -1:
                print("Error: Invalid HTTP response")
                return
            
            headers = response_data[:header_end].decode('utf-8')
            body = response_data[header_end + 4:]
            
            # Parse status line
            lines = headers.split('\r\n')
            status_line = lines[0]
            
            print(f"\nStatus: {status_line}")
            
            # Parse status code
            parts = status_line.split()
            if len(parts) < 2:
                print("Error: Invalid status line")
                return
            
            status_code = int(parts[1])
            
            # Check for errors
            if status_code != 200:
                print(f"\nServer returned error {status_code}")
                if body:
                    print(f"Response body:\n{body.decode('utf-8', errors='ignore')}")
                return
            
            # Get content type
            content_type = self.get_header(lines, 'Content-Type')
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {len(body)} bytes\n")
            
            # Handle based on content type
            if content_type and content_type.startswith('text/html'):
                # Print HTML content
                print("=" * 60)
                print("HTML Content:")
                print("=" * 60)
                print(body.decode('utf-8'))
                print("=" * 60)
            elif content_type and (content_type.startswith('application/pdf') or 
                                  content_type.startswith('image/')):
                # Save binary files
                self.save_file(body, content_type, save_dir)
            else:
                # Default: print as text
                print("=" * 60)
                print("Response Body:")
                print("=" * 60)
                print(body.decode('utf-8', errors='ignore'))
                print("=" * 60)
        
        except Exception as e:
            print(f"Error parsing response: {e}")
    
    def get_header(self, lines, header_name):
        """Extract header value from response"""
        header_name_lower = header_name.lower()
        for line in lines:
            if ':' in line:
                name, value = line.split(':', 1)
                if name.strip().lower() == header_name_lower:
                    return value.strip()
        return None
    
    def save_file(self, content, content_type, save_dir):
        """Save binary file to directory"""
        # Determine file extension
        ext_map = {
            'application/pdf': '.pdf',
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/gif': '.gif',
        }
        
        extension = '.bin'
        for mime, ext in ext_map.items():
            if content_type.startswith(mime):
                extension = ext
                break
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename
        import time
        filename = f"downloaded_{int(time.time())}{extension}"
        filepath = os.path.join(save_dir, filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(content)
        
        print(f"✓ File saved to: {filepath}")
        print(f"  Size: {len(content)} bytes")


def main():
    """Main entry point"""
    if len(sys.argv) != 5:
        print("Usage: python client.py <server_host> <server_port> <url_path> <save_directory>")
        print("\nExamples:")
        print("  python client.py localhost 8000 / ./downloads")
        print("  python client.py localhost 8000 /index.html ./downloads")
        print("  python client.py localhost 8000 /document.pdf ./downloads")
        print("  python client.py 192.168.1.100 8000 /books/book.pdf ./downloads")
        sys.exit(1)
    
    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    url_path = sys.argv[3]
    save_dir = sys.argv[4]
    
    # Ensure path starts with /
    if not url_path.startswith('/'):
        url_path = '/' + url_path
    
    client = HTTPClient()
    client.request(server_host, server_port, url_path, save_dir)


if __name__ == '__main__':
    main()
