# ESPWebServerAsync

This is an asynchronous version of [ESPWebServer](https://github.com/codemee/ESPWebServer/), implemented with MicroPython.

Most functions follow the original project.

## Installation

Just upload ESPWebServerAsync.py to your ESP8266/32 board and you're done.

## Usage

To use ESPWebServer.py library, you should:

1. Write functions as handlers for each path you'd like to serve contents. 

1. Start the server by calling begin(). 

1. Regsiter the handlers you just prepared by calling onPath().

1. You can also uploading HTML files onto somewhere in the filesystem and settnig the document path by calling setDocPath().

1. Call handleClient() repeatly to process requests.

### Documents and Templates

With setDocPath(), you can spcicified the path for all html files. For examples, if you call setDocPath('www'), and put index.html into /www, you can browse the file with 'http://server_ip/index.html to avoid accessing the project root. 

If you put a file with suffix '.p.html', the server would do formatting processing before output the content. You should first call setTplData() with a dictionary before accessing any template file, the server uses the elements in the dictionary to replacing all the formatting string in the template file.

If you access the document path without filename, the server would try to find out if there's a index.html or index.p.html file existed, and output the file. 

## Function reference

### begin(port)

Start the server at specified *port*.

### onPath(path, handler)

Legacy method to ensure compatibility. Calls `onGetPath(path, handler)`.

### onGetPath(path, handler)

Registers a handler for handling GET Requests.

The Handlers expected Method Signature: `methodName(socket, args)`

### onPostPath(path, handler)

Registers a handler for handling POST Requests.

The Handlers expected Method Signature: `methodName(socket, args, contenttype, content)`

### onPutPath(path, handler)

Registers a handler for handling PUT Requests.

The Handlers expected Method signature: `methodName(socket, args, contenttype, content)`

### setDocPath(path)

Specified the directory in the filesystem containing all the HTML files.

### setTplData(dic)

Specified the dictionary for template file. `dic` sould be a dictionary with all keys are string and contains all the names in replacing fields in all the template files.

### setMaxContentLength(size)

Defines the maximum Content Length of incoming request bodies (POST, PUT) in bytes. Default: 1024

### setRequestTimeout(sec)

Defines the timeout seconds of the requests. Default: 3

### setBaclog(backlog)

Defines the number of unaccepted connections that the system will allow before refusing new connections. Default: 16

### setHost(type) - Experimental

Defines the binding address of web server. Default: ESPWebServerAsync.ALL_IP
Options: ESPWebServerAsync.ALL_IP, ESPWebServerAsync.STA_IP, ESPWebServerAsync.AP_IP

### handleClient()

Check for new request and call corresponding handler to process it.

## Examples

You can upload www directory and index.p.html to "/" on ESP8266 board and run TestWebServer.py to see how it works.

`main.py` contains an example for handling POST Requests. PUT Requests are acting the same way.

TestWebServer.py will show its own IP address through serial monitor.Just open your browser and connect it to http://serverIP or http://serverIP/index.p.html, you'll get the main page that can turn on/off the buildin led on ESP8266 board. The main page also demonstrate the template file usage. 

You can also open http://serverip/www/index.html or http://serverip/www/ to view alternative version of controlling page that use AJAX to asynchronously turn on/off led.

You can use http://serverip/switch to switch led on/off led directly. Or you can use http://serverip/cmd?led=on to turn the led on and http://serverip/cmd?led=off to turn the led off.
