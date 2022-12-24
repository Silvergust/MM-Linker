import bpy
import websockets
import asyncio
import os
import mml_main as mml
import time
import mml_client
import json

class OBJECT_OT_send(bpy.types.Operator):
    """Send shader data to the MML program."""
    bl_idname = "image.mml_send"
    bl_label = "MML Send"
    data_to_send: bpy.props.StringProperty(name="data")
    image_name: bpy.props.StringProperty(name='image_name')
    expected_packets: bpy.props.IntProperty(name='expected_packets')
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print("Sending data: ")
        #mml_client.MMLClient.instance.send_command(mml.MML.commands_dict['connect'], self.image_name, self.data_to_send)
        data_dict = { "command" : "load_ptex", "image_name":self.image_name, "filepath" : self.data_to_send }
        data = json.dumps(data_dict)
        mml_client.MMLClient.instance.send_json(data)
        return {'FINISHED'}

#def manage_loop_and_connect(image_name, data_to_send, expected_packets):
#        if os.name == 'nt':
#            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # Possibly shouldn't be here
#        try:
#            loop = asyncio.get_running_loop()
#        except RuntimeError:
#            loop = None
#        print("loop: ", loop)
#        if loop and loop.is_running():
#            print("Loop is running")
#            loop.create_task(connect(image_name, data_to_send, expected_packets))
#        else:
#            asyncio.run(connect(image_name, data_to_send, expected_packets))
#            
#            
#async def connect(image_name, data_to_send, expected_packets):
#    print("connect")
#    print("Expected packets: ", expected_packets)
#    packets_to_send = []
#    t0 = time.time()
#    async with websockets.connect("ws://localhost:6000", max_size=1000000000) as websocket:
#        print("Connected")
#        await websocket.send(data_to_send)
#        websocket.close()
#        print("Data sent")           
#        
#        i = 0
#        while i < expected_packets:
#            i += 1
#            pkt = await websocket.recv()
#            print("Received response: ", pkt[:140])
#            packets_to_send.append(pkt)
#        img = bpy.data.images[image_name]
#        for pkt in packets_to_send:
#            mml.MML.interpret(img, pkt)
#    print("Connection time was ", time.time() - t0)
#    return