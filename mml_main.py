import bpy
import json
import mml_sender
import mml_client
import asyncio
import time


class MMLProperties(bpy.types.PropertyGroup):
    shader_code: bpy.props.StringProperty()
    ptex_filepath: bpy.props.StringProperty(name = "PTex Filepath", subtype='FILE_PATH')
    ptex_data: bpy.props.StringProperty(name="PTex Data")
    use_remote_parameters: bpy.props.BoolProperty(name="Use remote parameters")

def update_test(self, context):
        print("Value changed")
        if self.should_update:
            print("Updating.")
            data_to_send = str(self.name) + ":" + str(self.value)
            command_prefix = MML.commands_dict['set_remote_parameter_value'] if self.is_remote else MML.commands_dict['set_parameter_value']
            print("command_prefix: ", command_prefix)
            #mml_client.MMLClient.instance.send_command(MML.commands_dict['set_parameter_value'], self.owner_image.name, data_to_send)
            mml_client.MMLClient.instance.send_command(command_prefix, self.owner_image.name, data_to_send)

#types_enum =  [ ("INT", "Int") ]

class MMLParameters(bpy.types.PropertyGroup):
    label: bpy.props.StringProperty()
    value: bpy.props.StringProperty(update=update_test)
    owner_image: bpy.props.PointerProperty(type=bpy.types.Image)
    should_update: bpy.props.BoolProperty()
    is_remote: bpy.props.BoolProperty()
    #type: bpy.props.EnumProperty()
    

    
        
class OBJECT_OT_initialize(bpy.types.Operator):
    bl_idname = "image.mml_initialize"
    bl_label = "MML Initialize"
    image_name: bpy.props.StringProperty(name='image_name')
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        bpy.data.images[image_name].mml = MML()
        return {'FINISHED'}
    
    
class Commands:
    set_parameter_value = "0003"
    
    
class MML():
    command_size = 2
    commands_dict = {
        "connect" : "0001",
        "initialize_parameters" : "0002",
        "set_parameter_value" : "0003",
        "initialize_remote_parameters" : "0004",
        "set_remote_parameter_value" : "0005"
    }
    received_messages = []


    @classmethod
    def interpret(self, img, data):
        prefix = data[:MML.command_size]
        dummy, image_name, arguments = str(data).split("|")[:3] # WHen the image data is turned to a string, it may end up having another divider
        pad = 2 + 2 + len(image_name)
        if prefix.hex() == MML.commands_dict["connect"]: #"0001":
            print("pad: ", pad)
            MML.replace_image(image_name, data[pad:])
        elif prefix.hex() == MML.commands_dict["initialize_parameters"]:
            MML.initialize_parameters(image_name, data[pad:])
        elif prefix.hex() == MML.commands_dict["set_parameter_value"]:
            MML.set_parameter_values(image_name, data[pad:])
        elif prefix.hex() == MML.commands_dict["initialize_remote_parameters"]:
            MML.initialize_parameters(image_name, data[pad:], True)
        else:
            print("ERROR: first two bytes do not correspond to a valid prefix.")


    @classmethod
    def replace_image(self, image_name, data):
        img = bpy.data.images[image_name]
        print("replace_image, image: ", image_name)
        t0 = time.time()
        img.pixels.foreach_set([byte / 255.0 for byte in data])
        img.pack()
        img.update()
        bpy.context.view_layer.update()
        print("Image replaced in time: ", time.time() - t0)


    @classmethod
    def initialize_parameters(self, image_name, data, remote=False):
        print("initialize_parameters")
        print("Remote: ", remote)
        img = bpy.data.images[image_name]
        parameters = None
        if remote:
            parameters = img.mml_remote_parameters
        else:
            parameters = img.mml_local_parameters
        parameters.clear()
        #img.mml_remote_parameters.clear()
        string_data = data.decode('utf-8')
        print("string_data: ", string_data)
        json_data = json.loads(string_data)

        for entry in json_data:
            param_identifier = "{}/{}".format(entry['node'], entry['param_label'])
            #new_parameter = img.mml_remote_parameters.add()
            new_parameter = parameters.add()
            new_parameter.name = param_identifier
            new_parameter.node_name = entry['node']
            new_parameter.label = entry['param_label']
            new_parameter.owner_image = img
            parameters[param_identifier].should_update = False
            parameters[param_identifier].value = str(entry['param_value'])
            parameters[param_identifier].should_update = True
        return


    @classmethod
    def set_parameter_values(self, image_name, data):
        print("set_parameter_values()")
        img = bpy.data.images[image_name]