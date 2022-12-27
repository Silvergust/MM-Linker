import bpy
import json
import mml_sender
import mml_client
import asyncio
import time
import math


class MMLProperties(bpy.types.PropertyGroup):
    shader_code: bpy.props.StringProperty()
    ptex_filepath: bpy.props.StringProperty(name = "PTex Filepath", subtype='FILE_PATH')
    ptex_data: bpy.props.StringProperty(name="PTex Data")
    use_remote_parameters: bpy.props.BoolProperty(name="Use remote parameters")

def update_test(self, context):
        print("Value changed")
        if self.should_update:
            print("Updating.")
            #data_to_send = str(self.name) + ":" + str(self.value)
            #command_prefix = MML.commands_dict['set_remote_parameter_value'] if self.is_remote else MML.commands_dict['set_parameter_value']
            #print("command_prefix: ", command_prefix)
            #mml_client.MMLClient.instance.send_command(MML.commands_dict['set_parameter_value'], self.owner_image.name, data_to_send)
            #mml_client.MMLClient.instance.send_command(command_prefix, self.owner_image.name, data_to_send)
            data_to_send = json.dumps({ "command":"parameter_change", "parameter_label":self.name, "parameter_value":self.value, "image_name":self.owner_image.name, "render":"True", "parameter_type":"remote" if self.is_remote else "local" })
            mml_client.MMLClient.instance.send_json(data_to_send)

#types_enum =  [ ("INT", "Int") ]

class MMLParameters(bpy.types.PropertyGroup): # TODO: Control variable type for material nodes (MM doesn't handle them for "free" the way it does for other nodes)
    label: bpy.props.StringProperty()
    value: bpy.props.StringProperty(update=update_test)
    owner_image: bpy.props.PointerProperty(type=bpy.types.Image)
    should_update: bpy.props.BoolProperty()
    is_remote: bpy.props.BoolProperty()
    
        
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
#    commands_dict = {
#        "connect" : "0001",
#        "initialize_parameters" : "0002",
#        "set_parameter_value" : "0003",
#        "initialize_remote_parameters" : "0004",
#        "set_remote_parameter_value" : "0005",
#        "ping" : "0006"
#    }
    command_key_requirements = {
        "pong" : [],
        "replace_image" : ["image_name", "image_data"], # TODO: Make use of image names for proper identification
        "init_parameters" : ["image_name", "parameters_type", "parameters"],
        "inform" : ["info"],
        "request_parameters": ["image_name"]
    }
    info_message = ""
    received_messages = []
    is_ready = False

    @classmethod
    def key_check(self, data):
        if "command" not in data:
            print("ERROR: \"command\" key not found in data")
            return False
        for key in self.command_key_requirements[data["command"]]:
            if key not in data:
                print("ERROR: key \"{}\" not found in data".format(key))
                return False
        return True
        
    @classmethod
    def interpret(self, data):
        if data[:5] == b"json|":
            self.interpret_json(data[5:]) 
        elif data[:6] == b"image|":
            padding = int(data[6:9])
            image_name = str(data[10:padding-1])[2:-1]
            self.replace_image(image_name, data[padding:]) # TODO: Do away with the unnecessary copying
        else:
            print("Failed to interpret message")
        return
        
#        prefix = data[:MML.command_size]
#        dummy, image_name, arguments = str(data).split("|")[:3] # WHen the image data is turned to a string, it may end up having another divider
#        pad = 2 + 2 + len(image_name)
#        print(prefix.hex())
#        if prefix.hex() == MML.commands_dict["connect"]: #"0001":
#            print("pad: ", pad)
#            MML.replace_image(image_name, data[pad:])
#        elif prefix.hex() == MML.commands_dict["initialize_parameters"]:
#            MML.initialize_parameters(image_name, data[pad:])
#        elif prefix.hex() == MML.commands_dict["set_parameter_value"]:
#            MML.set_parameter_values(image_name, data[pad:])
#        elif prefix.hex() == MML.commands_dict["initialize_remote_parameters"]:
#            MML.initialize_parameters(image_name, data[pad:], True)
#        elif prefix.hex() == MML.commands_dict["ping"]:
#            print("Pong")
#        else:
#            print("ERROR: first two bytes do not correspond to a valid prefix.")

    @classmethod
    def interpret_json(self, data):
        data = json.loads(data)
        if not self.key_check(data):
            print("Key check fail")
            return
        command = data["command"]
        if command == "pong":
            print("Pong")
        elif command == "init_parameters":
            print("Initializing parameters ({})".format(data["parameters_type"]))
            MML.initialize_parameters(data)
        elif command == "inform":
            MML.info_message = data["info"]
        elif command == "request_parameters":
            data_to_send = { "command":"set_multiple_parameters", "parameters":[] }
            img = bpy.data.images[data["image_name"]]
            for parameter in img.mml_remote_parameters:
                parameter_data = json.dumps({ "parameter_label":parameter.name, "parameter_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "parameter_type":"remote"})
                data_to_send["parameters"].append(parameter_data)
            for parameter in img.mml_local_parameters:
                parameter_data = json.dumps({ "parameter_label":parameter.name, "parameter_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "parameter_type":"local"})
                data_to_send["parameters"].append(parameter_data)
                mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))


    @classmethod
    def replace_image(self, image_name, data):
        print("image_name: ", image_name)
        img = bpy.data.images[image_name]
        print("replace_image, image: ", image_name)
        t0 = time.time()
        print("Len(data): ", len(data))
        size = int(math.sqrt(len(data)))
        img.scale(size, size)
        #if len(img.pixels) != len(data):
        #    print("ERROR: Expected data of size {}, got {}".format(len(img.pixels), len(data)))
        #    return
        img.pixels.foreach_set(img.channels*[byte / 255.0 for byte in data])
        img.pack()
        img.update()
        bpy.context.view_layer.update()
        print("Image replaced in time: ", time.time() - t0)


    @classmethod
    def initialize_parameters(self, data, remote=False):
        print("initialize_parameters")
        print("Remote: ", remote)
        img = bpy.data.images[data["image_name"]]
        parameters = None
        if data["parameters_type"] == "remote":
            print("\n\n\n#### Remote")
            parameters = img.mml_remote_parameters
        elif data["parameters_type"] == "local":
            print("\n\n\n#### Local")
            parameters = img.mml_local_parameters
        else:
            print("\n\n\n#### Error")
            print("ERROR: Incorrect parameters type on initialization.")
        parameters.clear()
        received_parameters_data = data["parameters"]

        for entry in received_parameters_data:
            param_identifier = "{}/{}".format(entry['node'], entry['param_label'])
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