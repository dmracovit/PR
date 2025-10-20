"""
Multithreaded HTTP Server with Request Counter and Rate Limiting
Lab 2 - Protocols and Networks
"""
import os
import socket
import threading
import time
from collections import defaultdict, deque
from http_utils import (
    http_date, parse_request_line, split_http_message,
    resolve_path, guess_content_type
)

HOST = "0.0.0.0"
PORT = 8080
SERVER_NAME = "ConcurrentHTTP/1.0"
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW = 1.0

request_counter = defaultdict(int)
rate_limiter = defaultdict(lambda: deque(maxlen=RATE_LIMIT_REQUESTS))

counter_lock = threading.Lock()
rate_limit_lock = threading.Lock()

USE_THREAD_SAFE_COUNTER = True
SIMULATED_WORK_DELAY = 0.0


def build_http_response(status_code: int, status_text: str, body: bytes, content_type: str = "text/html; charset=utf-8") -> bytes:
    response_line = f"HTTP/1.0 {status_code} {status_text}\r\n"
    headers = (
        f"Date: {http_date()}\r\n"
        f"Server: {SERVER_NAME}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    )
    return response_line.encode() + headers.encode() + body


def build_error_response(status_code: int, status_text: str) -> bytes:
    body = f"<html><body><h1>{status_code} {status_text}</h1></body></html>".encode()
    return build_http_response(status_code, status_text, body)


def normalize_path_for_counter(path: str, is_dir: bool) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if is_dir and not path.endswith("/"):
        path += "/"
    elif not is_dir and path.endswith("/"):
        path = path.rstrip("/")
    return path


def increment_counter(path: str, is_dir: bool):
    normalized = normalize_path_for_counter(path, is_dir)
    
    if USE_THREAD_SAFE_COUNTER:
        with counter_lock:
            request_counter[normalized] += 1
    else:
        old_value = request_counter[normalized]
        time.sleep(0.01)
        request_counter[normalized] = old_value + 1


def check_rate_limit(client_ip: str) -> bool:
    current_time = time.time()
    
    with rate_limit_lock:
        timestamps = rate_limiter[client_ip]
        
        while timestamps and current_time - timestamps[0] > RATE_LIMIT_WINDOW:
            timestamps.popleft()
        
        if len(timestamps) >= RATE_LIMIT_REQUESTS:
            return True
        
        timestamps.append(current_time)
        return False


def serve_file(file_path: str) -> bytes:
    content_type = guess_content_type(file_path)
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return build_http_response(200, "OK", data, content_type)
    except Exception:
        return build_error_response(500, "Internal Server Error")


def serve_directory(url_path: str, dir_path: str, root: str) -> bytes:
    try:
        items = sorted(os.listdir(dir_path))
    except Exception:
        return build_error_response(500, "Internal Server Error")
    
    if not url_path.endswith("/"):
        url_path += "/"
    
    template_path = os.path.join(TEMPLATE_DIR, "directory.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception:
        return build_error_response(500, "Template Error")
    
    lines = []
    
    if os.path.realpath(dir_path) != os.path.realpath(root):
        parent = "/".join(url_path.rstrip("/").split("/")[:-1])
        if not parent:
            parent = "/"
        lines.append(f'        <li class="dir"><a href="{parent}">..</a></li>')
    
    for name in items:
        item_url = url_path + name
        item_path = os.path.join(dir_path, name)
        
        if os.path.isdir(item_path):
            item_url += "/"
            count = request_counter[item_url]
            lines.append(f'        <li class="dir"><a href="{item_url}">{name}/</a><span class="counter">{count} hits</span></li>')
        else:
            count = request_counter[item_url]
            lines.append(f'        <li class="file"><a href="{item_url}">{name}</a><span class="counter">{count} hits</span></li>')
    
    html = template.replace("{{PATH}}", url_path)
    html = html.replace("{{ITEMS}}", "\n".join(lines))
    
    return build_http_response(200, "OK", html.encode("utf-8"))


def handle_request(conn: socket.socket, root: str):
    try:
        conn.settimeout(10)
        
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        
        headers, _ = split_http_message(data)
        lines = headers.split(b"\r\n")
        
        if not lines:
            conn.sendall(build_error_response(400, "Bad Request"))
            return
        
        method, path, version = parse_request_line(lines[0].decode("iso-8859-1", errors="replace"))
        
        if not method or not path:
            conn.sendall(build_error_response(400, "Bad Request"))
            return
        
        if method != "GET":
            conn.sendall(build_error_response(405, "Method Not Allowed"))
            return
        
        client_ip = conn.getpeername()[0]
        if check_rate_limit(client_ip):
            conn.sendall(build_error_response(429, "Too Many Requests"))
            return
        
        time.sleep(SIMULATED_WORK_DELAY)
        
        real_path, is_directory = resolve_path(root, path)
        
        if not real_path:
            conn.sendall(build_error_response(404, "Not Found"))
            return
        
        if is_directory and not path.endswith("/"):
            path += "/"
        
        increment_counter(path, is_directory)
        
        if is_directory:
            response = serve_directory(path, real_path, root)
        else:
            response = serve_file(real_path)
        
        conn.sendall(response)
        
    except Exception as e:
        print(f"Error handling request: {e}")
        try:
            conn.sendall(build_error_response(500, "Internal Server Error"))
        except:
            pass
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except:
            pass
        conn.close()


def run_server(root: str, port: int = PORT, use_threading: bool = True):
    print(f"Server: {SERVER_NAME}")
    print(f"Serving: {root}")
    print(f"Port: {port}")
    print(f"Multithreaded: {use_threading}")
    print(f"Thread-safe counter: {USE_THREAD_SAFE_COUNTER}")
    print(f"Simulated work delay: {SIMULATED_WORK_DELAY}s")
    print(f"Rate limit: {RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s per IP")
    print()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, port))
    server_socket.listen(10)
    
    print(f"Listening on {HOST}:{port}...")
    print()
    
    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")
            
            if use_threading:
                thread = threading.Thread(target=handle_request, args=(conn, root), daemon=True)
                thread.start()
            else:
                handle_request(conn, root)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multithreaded HTTP Server")
    parser.add_argument("directory", help="Directory to serve")
    parser.add_argument("--port", type=int, default=PORT, help="Port to listen on")
    parser.add_argument("--single-threaded", action="store_true", help="Run in single-threaded mode (for comparison)")
    
    args = parser.parse_args()
    
    root_dir = os.path.abspath(args.directory)
    use_threading = not args.single_threaded
    
    run_server(root_dir, args.port, use_threading)
