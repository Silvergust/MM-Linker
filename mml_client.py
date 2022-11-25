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
            while True:
                while len(websocket.messages) > 0:
                    message = websocket.messages.popleft()
                    print("Handling message ", message[:140])
                    mml.MML.interpret(self.image, message)
                if len(self.data_to_send) > 0:
                    await websocket.send(self.data_to_send.pop())
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
        