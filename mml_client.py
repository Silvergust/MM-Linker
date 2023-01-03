import bpy
import time
import asyncio 
import websockets
import threading
import mml_main as mml
import json

class Status:
    disconnected = 0
    connected = 1
    
class MMLClient:
    instance = None
    #port = 6001
#    port = 6001
    #port = bpy.props.IntProperty(name="Port")
    status_strings = {
        Status.disconnected : "Disconnected",
        Status.connected : "Connected"
    }
    
    def __init__(self): # At some point I'll have to do without an img argument/field, tentatively here for the purpose of testing.
        if MMLClient.instance == None:
            MMLClient.instance = self
        elif MMLClient.instance != self:
            del self
            return
        self.status = Status.disconnected
        self.data_to_send = []
        #self.begin_connect_thread()
        #self.port = bpy.props.IntProperty(name="Port")
        
    def begin_connect_thread(self):
        if self.status == Status.connected:
            return
        connection = threading.Thread(target = self.start_connection)
        connection.daemon = True
        connection.start()
    
    def start_connection(self):
        print("Start connection")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect(None))
        loop.close()
        
    async def connect(self, data):
        print("Connect()")
        
        async with websockets.connect("ws://localhost:{}".format(str(self.port)), max_size=1000000000) as websocket:
            self.status = Status.connected
            print("Connected")
            previous_time = time.time()
            while True:
                if not websocket.open:
                    self.status = Status.disconnected
                    break
                while len(websocket.messages) > 0:
                    message = websocket.messages.popleft()
                    #print("Handling message ", message[:140])
                    mml.MML.interpret(message)
                if len(self.data_to_send) > 0:
                    await websocket.send(self.data_to_send.pop())
                if time.time() > previous_time + 5.0:
                    previous_time = time.time()
                    data = json.dumps({"command":"ping"})
                    self.send_json(data)
                await asyncio.sleep(0.01)
            print("Disconnected from MM")
            mml.MML.on_disconnect()
        
            
    def send(self, data):
        self.data_to_send.append(data)
        
    def send_json(self, data):
        self.data_to_send.append(data)
        
        
    def send_command(self, command, image_name, data):
        self.data_to_send.append("{}|{}|{}".format(command, image_name, data))
         
    def get_status_string(self):
        return MMLClient.status_strings[self.status]
        
class OBJECT_OT_connect(bpy.types.Operator):
    """Attempt to connect MML client to server."""
    bl_idname = "image.mml_connect"
    bl_label = "MML Connect"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        MMLClient.instance.begin_connect_thread()
        return {'FINISHED'}