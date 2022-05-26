import ESPWebServerAsync
import network
import machine

GPIO_NUM = 2 # Builtin led (D4)
# Get pin object for controlling builtin LED
pin = machine.Pin(GPIO_NUM, machine.Pin.OUT)
pin.on() # Turn LED off (it use sinking input)

# Dictionary for template file
ledData = {
    "title":"Remote LED",
    "color":"red",
    "status":"Off",
    "switch":"on"
}

# Update information
def updateInfo(writer):
    global ledData, color, status, switch
    ledData["color"] = "red" if pin.value() else "green"
    ledData["status"] = "Off" if pin.value() else "On"
    ledData["switch"] = "on" if pin.value() else "off"
    yield from ESPWebServerAsync.ok(
        writer,
        "200",
        ledData["status"])

def handleStop(writer):
    yield from ESPWebServerAsync.ok(
        writer,
        "200",
        "stopped")
    running = False
    yield from ESPWebServerAsync.close()

def handlePost(writer, args, contenttype, content):
    yield from ESPWebServerAsync.ok(
        writer,
        "200",
        contenttype+" "+content.decode('UTF-8'))

# Handler for path "/cmd?led=[on|off]"
def handleCmd(writer, args):
    if 'led' in args:
        if args['led'] == bytes('on','utf-8'):
            pin.off()
        elif args['led'] == bytes('off','utf-8'):
            pin.on()
        return updateInfo(writer)
    else:
        ESPWebServerAsync.err(writer, "400", "Bad Request")

# handler for path "/switch"
def handleSwitch(writer, args):
    pin.value(not pin.value()) # Switch back and forth
    return updateInfo(writer)


server = ESPWebServerAsync.server()

# ESPWebServerAsync.begin(8899)
# Start the server @ port 8899
server.begin() # use default 80 port

# Register handler for each path
# ESPWebServerAsync.onPath("/", handleRoot)
server.onPath("/cmd", handleCmd)
server.onPath("/switch", handleSwitch)
server.onPostPath("/post", handlePost)

# Setting the path to documents
server.setDocPath("/")

# Setting data for template
server.setTplData(ledData)

# Setting maximum Body Content Size. Set to 0 to disable posting. Default: 1024
server.setMaxContentLength(1024)

# Let server process requests
server.handleClient()

server.close()