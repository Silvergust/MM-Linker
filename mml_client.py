import time
import asyncio 
import threading
import json
import bmesh

if "bpy" in locals():
    import importlib
    importlib.reload(websockets)
    importlib.reload(mml_main)
else:
    import bpy
    from . import websockets
    from . import mml_main

class Status:
    disconnected = 0
    connected = 1
    
class MMLClient:
    instance = None
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
                    mml_main.MML.interpret(message)
                if len(self.data_to_send) > 0:
                    await websocket.send(self.data_to_send.pop())
                if time.time() > previous_time + 20.0:
                    previous_time = time.time()
                    data = json.dumps({"command":"ping"})
                    self.send_json(data)
                await asyncio.sleep(0.01)
            mml_main.MML.inform("Disconnected from MM")
            mml_main.MML.on_disconnect()
        
            
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


class OBJECT_OT_update_islands(bpy.types.Operator):
    """Attempt to connect MML client to server."""
    bl_idname = "image.mml_update_islands"
    bl_label = "MML Update Islands"
    
    @classmethod
    def poll(cls, context):
        return context.object and context.mode == 'EDIT_MESH'


    def execute(self, context):
        #img = bpy.context.area.spaces.active.image
        #print(dir(bpy.context.area.spaces.active))
        #print(bpy.context.area.spaces.active.uv_editor)
        #print(dir(bpy.context.area.spaces.active.uv_editor))
        bm = bmesh.from_edit_mesh(context.object.data)
        verts = bm.verts[:]
        islands = []
        while len(verts) > 0:
            #print("vert[0]: ", verts[0])
            island = mml_main.Island(bm, bm.loops.layers.uv[0], verts[0])
            #print("island.get_vertices(): ")
            #print(island.get_vertices())
            verts = list(set(verts).difference(set(island.get_vertices())))
            #print("island verts:")
            #print(verts)
            islands.append(island)
        for island in islands:
            print("Island:")
            print(island)
        return {'FINISHED'}
