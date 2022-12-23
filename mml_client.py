import bpy
import time
import asyncio 
import websockets
import threading
import mml_main as mml

class Status:
    disconnected = 0
    connected = 1
    
class MMLClient:
    instance = None
    
    status_strings = {
        Status.disconnected : "Disconnected",
        Status.connected : "Connected"
    }
    
    def __init__(self, image): # At some point I'll have to do without an img argument/field, tentatively here for the purpose of testing.
        if MMLClient.instance == None:
            MMLClient.instance = self
        elif MMLClient.instance != self:
            del self
            return
        self.image = image
        self.status = Status.disconnected
        self.data_to_send = []
        self.begin_connect_thread()
        
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
        
        async with websockets.connect("ws://localhost:6000", max_size=1000000000) as websocket:
            self.status = Status.connected
            print("Connected")
            previous_time = time.time()
            while True:
                if not websocket.open:
                    self.status = Status.disconnected
                    break
                while len(websocket.messages) > 0:
                    message = websocket.messages.popleft()
                    print("Handling message ", message[:140])
                    mml.MML.interpret(self.image, message)
                if len(self.data_to_send) > 0:
                    await websocket.send(self.data_to_send.pop())
                if time.time() > previous_time + 5.0:
                    previous_time = time.time()
                    self.send(mml.MML.commands_dict["ping"] + "||")
                await asyncio.sleep(0.01)
            print("End")
        
            
    def send(self, data):
        print("Send()")
        self.data_to_send.append(data)
        
    def send_command(self, command, image_name, data):
        print("send_command_data")
        self.data_to_send.append("{}|{}|{}".format(command, image_name, data))
         
    def get_status_string(self):
        return MMLClient.status_strings[self.status]
        
class OBJECT_OT_connect(bpy.types.Operator):
    """Attempt to connect MML client to server."""
    bl_idname = "image.mml_connect"
    bl_label = "MML Connect"
    #data_to_send: bpy.props.StringProperty(name="data")
    #image_name: bpy.props.StringProperty(name='image_name')
    #expected_packets: bpy.props.IntProperty(name='expected_packets')
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        MMLClient.instance.begin_connect_thread()
#        print("Sending data: ")
#        #MMLClient.instance.send_command(mml.MML.commands_dict['connect'], self.image_name, self.data_to_send)
#        connection = threading.Thread(target = MMLClient.instance.start_connection)
#        connection.daemon = True
#        connection.start()
        return {'FINISHED'}