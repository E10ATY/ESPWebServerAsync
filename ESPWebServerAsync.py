# A simple HTTP server
# It adopt the programming style of ESP8266WebServer 
# library in ESP8266 Arduino Core

import gc
import machine
import network
import os
import time
import uasyncio as asyncio

import esp
esp.osdebug(None)

ALL_IP = 0
STA_IP = 1
AP_IP = 2

# MIME types
mimeTypes = {
    ".css" :"text/css",
    ".gif" :"image/gif",
    ".htm" :"text/html",
    ".html":"text/html",
    ".ico" :"image/x-icon",
    ".jpg" :"image/jpeg",
    ".js"  :"application/javascript",
    ".json":"application/json",
    ".png" :"image/png",
    ".svg" :"image/svg+xml",
    ".txt" :"text/plain",
    ".xml" :"application/xml",
}

# Respong error meesage to client
# use: yield from ESPWebServerAsync.err( ... )
def err(writer, code, message):
    print("                      - [" + code + "] " + message)
    yield from writer.awrite("HTTP/1.1 " + code + " " + message + "\r\n")
    yield from writer.awrite("Content-Type: text/html\r\n\r\n")
    yield from writer.awrite("<h1>" + message + "</h1>")
    yield from writer.aclose()
    
    
# Response successful message or webpage to client
# use: yield from ESPWebServerAsync.ok( ... )
def ok(writer, code, *args):
    if len(args)==1:
        content_type = "text/plain"
        msg = args[0]
    elif len(args)==2:
        content_type = args[0]
        msg = args[1]
    else:
        raise TypeError("ok() takes 3 or 4 positional arguments but "+ str(len(args)+2) +" were given")

    # msgLength = self._checkFileSize(msg)
    # if msgLength != None:
        # yield from writer.awrite("Content-length: " + msgLength + "\r\n")
        # _sendPage(writer, msg)
    # else:
    msgLength = len(msg)
    print("                      - [" + code + "] BodyLen: " + str(msgLength))
    yield from writer.awrite("HTTP/1.1 " + code + " OK\r\n")
    yield from writer.awrite("Content-Type: " + content_type + "\r\n")
    yield from writer.awrite("Content-length: " + str(msgLength) + "\r\n\r\n")
    yield from writer.awrite(msg)
    yield from writer.aclose()

class server:
    # Dict for registed GET handlers of all paths
    _getHandlers = {}
    
    # Dict for registed POST handlers of all paths
    _postHandlers = {}
    
    # Dict for registed PUT handlers of all paths
    _putHandlers = {}
    
    # Function of handler for request not found
    _notFoundHandler = None
    
    # The path to the web documents on MicroPython filesystem
    _docPath = ""
    
    # Data for template
    _tplData = {}
    
    # Max. POST/PUT-Data size
    _maxContentLength = 1024
    
    # Request Timeout
    _request_timeout = 3
    
    # Backlog
    _backlog = 16
    
    # Host
    _host = '0.0.0.0'
    
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._explicit_url_map = {}
        self._parameterized_url_map = {}
        self._conns = {}
        self._processed_connections = 0
        
    def begin(self, port=80):
        # self._server_coro = self._tcp_server(port)
        # self._loop.create_task(self._server_coro)
        this = self
        
        self._loop.create_task(asyncio.start_server(
            self._serve, self._host, port, self._backlog
        ))

    def handleClient(self):
        self._loop.run_forever()
        self._loop.close()

    def close(self):
        asyncio.cancel(self._server_coro)
        # for hid, coro in self._conns.items():
            # asyncio.cancel(coro)
        
    def onPath(self, path, handler):
        """Register handler for processing GET request of specified path,
        Here to ensure compatibility.
        """
        self.onGetPath(path, handler)

    def onGetPath(self, path, handler):
        """Register handler for processing GET request of specified path
        """
        self._getHandlers[path] = handler

    def onPostPath(self, path, handler):
        """Register handler for processing POST of specified path
        """
        self._postHandlers[path] = handler
        
    def onPutPath(self, path, handler):
        """Register handler for processing PUT of specified path
        """
        self._putHandlers[path] = handler
        
    def onNotFound(self, handler):
        """Register handler for processing request of not found path
        """
        self._notFoundHandler = handler

    def setDocPath(self, path):
        """Set the path to documents' directory
        """
        if path.endswith("/"):
            self._docPath = path[:-1]
        else:
            self._docPath = path

    def setTplData(self, data):
        """Set data for template
        """
        self._tplData = data

    def setMaxContentLength(self, max):
        """Set the maximum content lenpth for incomming data bodies
        """
        self._maxContentLength = max

    def setRequestTimeout(self, request_timeout):
        """Set the request timeout for connections
        """
        self._request_timeout = request_timeout
        
    def setBacklog(self, backlog):
        """Set the number of unaccepted connections that the system will allow before refusing new connections.
        """
        self._backlog = backlog
    
    def setHost(self, host):
        """Set the ip address to bind.
        """
        if host == STA_IP:
            self._host = network.WLAN(network.STA_IF).ifconfig()[0]
        elif host == AP_IP:
            self._host = network.WLAN(network.AP_IF).ifconfig()[0]
        else: # ALL_IP
            self._host = '0.0.0.0'
            
    def _serve(self, reader, writer):
        gc.collect()
        try:
            while(yield from self._handler(reader, writer)):
                gc.collect()
        finally:
            yield from writer.aclose()
            gc.collect()

    async def _handler(self, reader, writer):
        gc.collect()

        try:
            yield from asyncio.wait_for(self._handle_request(reader, writer),
                                        self._request_timeout)
            
        except asyncio.CancelledError as e:
            # print("[_handler][CancelledError]", e, " - {}:{}".format(*reader.get_extra_info('peername')))
            pass
        except asyncio.TimeoutError as e:
            # print("[_handler][TimeoutError]", e, " - {}:{}".format(*reader.get_extra_info('peername')))
            pass
        except Exception as e:
            print("[_handler][Exception]", e, " - {}:{}".format(*reader.get_extra_info('peername')))
            pass
        finally:
            yield from writer.aclose()
            
    async def _handle_request(self, reader, writer):
        try: 
            firstLine = yield from reader.readline()
            firstLine = firstLine.decode('utf-8')
        except Exception as e:
            print("[_handle_request][Exception]First Line:", e, " - {}:{}".format(*reader.get_extra_info('peername')))
            firstLine = "" 
        partFirstLine = firstLine.split();
        
        if len(partFirstLine) != 3:
            return

        (httpMethod, httpUrl, httpVersion) = partFirstLine

        if "?" in httpUrl:
            (path, query) = httpUrl.split("?", 2)
        else:
            (path, query) = (httpUrl, "")

        args = {}
        contentType = ""
        content = b""
        contentLength = 0

        if query: # Parsing the querying string
            argPairs = query.split("&")
            for argPair in argPairs:
                arg = argPair.split("=")
                args[arg[0]] = self._unquote(arg[1])

        while True: # Read until blank line after header
            gc.collect()
            
            header = yield from reader.readline()
            if header.startswith(b"Content-Length"):
                (key, contentLengthStr) = str(header).split(" ")
                contentLength = int(contentLengthStr[0:-5])
                if (contentLength > self._maxContentLength):
                    yield from err(writer, "400", "Bad Request")
                    return
            if (header.startswith(b"Content-Type")):
                (key, contentType) = str(header).split(" ")
                contentType = contentType[0:-5]
            if (header == b""):
                return
            if (header == b"\r\n" and contentLength > 0):
                while(len(content) < contentLength):
                    newContent = yield from reader.read(contentLength)
                    content = content + newContent
                    if (len(content) > self._maxContentLength):
                        yield from err(writer, "400", "Bad Request")
                        return
                break
            elif header == b"\r\n":
                break
        
        # Show information to console
        print("[{}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}]".format(*time.localtime()),
                httpMethod, httpUrl, httpVersion,
                "{}:{}".format(*reader.get_extra_info('peername')))
        
        # Check for supported HTTP version
        if httpVersion != "HTTP/1.0" and httpVersion != "HTTP/1.1":
            yield from err(writer, "505", "Version Not Supported")
        elif (httpMethod != "GET" and httpMethod != "PUT" and httpMethod != "POST"):
            yield from err(writer, "501", "Not Implemented")
        elif (path in self._postHandlers and httpMethod == "POST"):
            yield from self._postHandlers[path](writer, args, contentType, content)
        elif (path in self._putHandlers and httpMethod == "PUT"):
            yield from self._putHandlers[path](writer, args, contentType, content)
        elif (path in self._getHandlers and httpMethod == "GET"):
            yield from self._getHandlers[path](writer, args)
        elif path in self._getHandlers:
            yield from self._getHandlers[path](writer, args)
        else: # find file in the document path
            yield from self._serveFile(writer, path)
        yield from writer.aclose()
        
    def _checkFileSize(self,path):
        try:
            stat = os.stat(path)
            # stat[0] bit 15 / 14 -> file/dir
            if stat[0] & 0x8000 == 0x8000: # file
                fileSize = stat[6]
            elif stat[0] & 0x4000 == 0x4000: # dir
                fileSize = -1
            else:
                fileSize = None
            return fileSize
        except OSError as e: # File not found
            return None
        except Exception as e:
            print("ERROR:[chkfs] path: "+path+", errmsg:",e)
            return None
            
    def _serveFile(self, writer, path):
        # Serves a text file from the filesystem
        filePath = self._docPath + path
        fileFound = True
        
        fileSize = self._checkFileSize(filePath)
        if (fileSize != None and fileSize < 0):
            if not path.endswith("/"):
                print("                      - Url redirect: " + path)
                yield from writer.awrite("HTTP/1.1 301 Moved Permanently\r\n")
                yield from writer.awrite("Location: " + path + "/\r\n\r\n")
                return
            fileSize = None

        if fileSize == None:
            if not path.endswith("/"):
                fileFound = False
            else:
                filePath = self._docPath + path + "index.html"
                
                # find index.html in the path
                fileSize = self._checkFileSize(filePath)
                if fileSize == None:
                    filePath = self._docPath + path + "index.p.html"
                    
                    # find index.p.html in the path
                    fileSize = self._checkFileSize(filePath)
                    if fileSize == None:
                        fileFound = False
        
        if not fileFound: # file or default html file specified in path not found
            if self._notFoundHandler:
                self._notFoundHandler(writer)
            else:
                yield from err(writer, "404", "Not Found")
            return
        
        if(filePath != self._docPath + path):
            print("                      - Path rewrite: " + filePath)
        
        # Responds the header first
        yield from writer.awrite("HTTP/1.1 200 OK\r\n")
        contentType = "application/octet-stream"
        for ext in mimeTypes:
            if filePath.endswith(ext):
                contentType = mimeTypes[ext]
        yield from writer.awrite("Content-Type: " + contentType + "\r\n")
        yield from writer.awrite("Content-length: " + str(fileSize) + "\r\n\r\n")
        
        # Responds the file content
        if filePath.endswith(".p.html"):
            with open(filePath, "r") as f:
                gc.collect()
                for l in f:
                    yield from writer.awrite(l.format(**self._tplData))
        else:
            yield from self._sendPage(writer, filePath)

    def _sendPage(self, writer, filePath):
        # Send a binary file content from the filesystem
        try:
            with open(filePath, "rb") as f:
                gc.collect()
                buf = bytearray(128)
                while True:
                    size = f.readinto(buf)
                    if size == 0:
                        break
                    yield from writer.awrite(buf, sz=size)
        except Exception as e:
            print("[_sendPage][Exception]", e, " - {}:{}".format(*writer.get_extra_info('peername')))

    def _unquote(self, string):
        # unquote_to_bytes('abc%20def') -> b'abc def'."""
        if not string:
            string.split
            return b''
        if isinstance(string, str):
            string = string.encode('utf-8')
        bits = string.split(b'%')
        if len(bits) == 1:
            return string
        res = [bits[0]]
        append = res.append
        for item in bits[1:]:
            try:
                append(bytes([int(item[:2], 16)]))
                append(item[2:])
            except KeyError:
                append(b'%')
                append(item)
        return b''.join(res)

