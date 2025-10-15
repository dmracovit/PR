# PR Lab 1: HTTP File Server

Laboratory Work 1 - Programming and Concurrency
Faculty: FAF-23x

## Prerequisites

**Before running the project, make sure:**
1. ✅ Docker Desktop is installed on your Mac
2. ✅ **Docker Desktop is RUNNING** (check menu bar for Docker icon)
3. ✅ You have added your PDF and image files to the `www/` directory

## Overview

This project implements a simple HTTP file server from scratch using Python and TCP sockets. The server can serve HTML, PDF, and PNG files, generate directory listings, and handle HTTP GET requests.

## 🎯 Features Implemented

### Core Requirements (Grade 5-7):
- ✅ HTTP file server using TCP sockets (no http.server library)
- ✅ Parse HTTP GET requests
- ✅ Serve HTML, PDF, and PNG files with correct MIME types
- ✅ Return 404 for non-existent files
- ✅ Directory as command-line argument
- ✅ Docker Compose setup

### Bonus Features (Grade 10):
- ✅ **HTTP Client** (+2 pts) - Download files or print HTML
- ✅ **Directory Listing** (+2 pts) - Auto-generate HTML for directories
- ⬜ **Friend's Server** (+1 pt) - Browse friend's server on local network

## 🏗️ Architecture

### How It Works

```
┌─────────────┐         HTTP Request          ┌─────────────┐
│   Browser   │ ──────────────────────────────>│   Server    │
│  (Client)   │                                 │  (Python)   │
│             │<─────────────────────────────── │             │
└─────────────┘         HTTP Response          └─────────────┘
                        (HTML/PDF/PNG)                 │
                                                       │
                                                       ▼
                                              ┌─────────────┐
                                              │  www/       │
                                              │  directory  │
                                              └─────────────┘
```

### Server Flow:

1. **Socket Creation** - Creates TCP socket on port 8000
2. **Listen** - Waits for incoming connections
3. **Accept** - Accepts client connection
4. **Receive** - Reads HTTP request from client
5. **Parse** - Extracts method (GET) and path (e.g., /index.html)
6. **Process**:
   - If path is a file → Read file and send with correct Content-Type
   - If path is a directory → Generate HTML listing
   - If path doesn't exist → Send 404 error
7. **Send** - Sends HTTP response with headers and body
8. **Close** - Closes client connection
9. **Loop** - Goes back to step 3

### Key Components:

**server.py**
- `HTTPServer` class handles all server logic
- `handle_request()` - Processes incoming HTTP requests
- `serve_file()` - Reads and serves individual files
- `serve_directory()` - Generates HTML directory listings
- `get_content_type()` - Maps file extensions to MIME types
- `send_response()` - Constructs and sends HTTP responses

**client.py**
- `HTTPClient` class for making HTTP requests
- Connects to server via TCP socket
- Sends GET requests
- Parses responses and handles based on Content-Type:
  - HTML → prints to console
  - PDF/PNG → saves to directory

## 🐳 Project Structure

```
PR/
├── server.py              # HTTP server implementation
├── client.py              # HTTP client implementation
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Docker orchestration
├── README.md             # This file
└── www/                  # Content directory (served files)
    ├── index.html        # Homepage
    ├── *.png             # Images
    ├── *.pdf             # PDF documents
    └── books/            # Subdirectory example
        ├── *.pdf
        └── *.png
```

## 🚀 How to Run

### Option 1: Using Docker Compose (Required for submission)

1. **Start the server:**
```bash
docker-compose up --build
```

2. **Open browser and visit:**
- Main page: http://localhost:8000/
- Directory listing: http://localhost:8000/books/
- Direct file: http://localhost:8000/index.html

3. **Stop the server:**
```bash
docker-compose down
```

### Option 2: Run Directly with Python (for testing)

1. **Start the server:**
```bash
python3 server.py ./www 8000
```

2. **Open browser:** http://localhost:8000/

### Testing the Client

**In another terminal** (while server is running):

```bash
# Request HTML page (prints to console)
python3 client.py localhost 8000 / ./downloads

# Download a PDF
python3 client.py localhost 8000 /sample.pdf ./downloads

# Download an image
python3 client.py localhost 8000 /library.png ./downloads

# Browse subdirectory
python3 client.py localhost 8000 /books/ ./downloads
```

### Testing with Docker

**Run client inside the container:**
```bash
docker-compose exec http-server python client.py localhost 8000 / /app/downloads
```

## 🧪 Testing Scenarios

### 1. Test HTML File
**Browser:** http://localhost:8000/index.html  
**Expected:** Homepage displays with images

### 2. Test PNG Image
**Browser:** http://localhost:8000/yourimage.png  
**Expected:** Image displays in browser

### 3. Test PDF File
**Browser:** http://localhost:8000/document.pdf  
**Expected:** PDF opens/downloads

### 4. Test 404 Error
**Browser:** http://localhost:8000/nonexistent.pdf  
**Expected:** "404 Not Found" message

### 5. Test Directory Listing
**Browser:** http://localhost:8000/ or http://localhost:8000/books/  
**Expected:** HTML page with clickable file links

### 6. Test Client
**Terminal:**
```bash
python3 client.py localhost 8000 /index.html ./downloads
```
**Expected:** HTML content printed to console

## 📡 HTTP Protocol Details

### Example HTTP Request (from browser):
```
GET /index.html HTTP/1.1
Host: localhost:8000
User-Agent: Mozilla/5.0
Accept: text/html
```

### Example HTTP Response (from server):
```
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 5678
Connection: close

<html>...</html>
```

### Supported MIME Types:
- `text/html` - HTML pages
- `application/pdf` - PDF documents
- `image/png` - PNG images
- `image/jpeg` - JPEG images
- `image/gif` - GIF images

## 🔧 Technical Implementation

### Socket Programming Basics:

```python
# Server side
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(5)
client_socket, address = server_socket.accept()

# Client side
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8000))
```

### HTTP Request Parsing:
```python
request_data = client_socket.recv(4096).decode('utf-8')
request_line = request_data.split('\r\n')[0]
method, path, version = request_line.split()
```

### HTTP Response Construction:
```python
response = f"HTTP/1.1 {status_code} {status_text}\r\n"
response += f"Content-Type: {content_type}\r\n"
response += f"Content-Length: {len(body)}\r\n"
response += "\r\n"
client_socket.sendall(response.encode() + body)
```

## 📊 Lab Report Checklist

For your submission, include screenshots of:

- ✅ Source directory structure (`ls -la`)
- ✅ Docker compose file contents
- ✅ Starting the container (`docker-compose up`)
- ✅ Server running (terminal output)
- ✅ Contents of served directory (`ls www/`)
- ✅ Browser request: 404 error (nonexistent file)
- ✅ Browser request: HTML file with embedded image
- ✅ Browser request: PDF file
- ✅ Browser request: PNG image
- ✅ Directory listing page (main and subdirectory)
- ✅ Client output: HTML request
- ✅ Client output: Downloaded PDF/PNG files
- ⬜ Friend's server: IP discovery, browsing their files

## 🎓 Theoretical Questions to Prepare

1. **What is a TCP socket?**
2. **Explain the HTTP request/response cycle**
3. **What is the difference between TCP and UDP?**
4. **What are HTTP status codes? (200, 404, 500)**
5. **What is a MIME type?**
6. **How does socket.listen() work?**
7. **What is the purpose of bind() in socket programming?**
8. **Explain the three-way handshake in TCP**
9. **What happens when you type a URL in the browser?**
10. **How does the server handle multiple clients?** (Answer: One at a time - single-threaded)

## 🌐 Testing with a Friend

To browse a friend's server on the same network:

1. **Find your IP address:**
```bash
# macOS/Linux
ifconfig | grep "inet "
# or
ipconfig getifaddr en0
```

**Author:** Racovita Dumitru 
**Date:** October 14, 2025  
**Repository:** https://github.com/dmracovit/PR