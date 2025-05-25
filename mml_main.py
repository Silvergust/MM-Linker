import json
import asyncio
import time
import math
#import bmesh
from mathutils import Vector
from mathutils import geometry as geo

if "bpy" in locals():
    import importlib
    importlib.reload(mml_client)
    importlib.reload(mml_sender)
else:
    import bpy
    from . import mml_client
    from . import mml_sender


class MMLProperties(bpy.types.PropertyGroup):
    port: bpy.props.IntProperty(name="Port", default=6001) # Unfortunately couldn't go on something more sensible like MMLClient
    ptex_filepath: bpy.props.StringProperty(name = "PTex Filepath", subtype='FILE_PATH')
    island_only: bpy.props.BoolProperty(name = "Selected Island Only")
    island_data: bpy.props.StringProperty(name = "Island Data")
    use_remote_parameters: bpy.props.BoolProperty(name="Use remote parameters")
    auto_update: bpy.props.BoolProperty(name="Auto-Update")
    request_albedo: bpy.props.BoolProperty(name="Request albedo map")
    request_metallicity: bpy.props.BoolProperty(name="Request metallicity map")
    request_roughness: bpy.props.BoolProperty(name="Request roughness map")
    request_emission: bpy.props.BoolProperty(name="Request emission map")
    request_normal: bpy.props.BoolProperty(name="Request normal map")
    request_occlusion: bpy.props.BoolProperty(name="Request ambient occlusion map")
    request_depth: bpy.props.BoolProperty(name="Request depth map")
    request_transparency: bpy.props.BoolProperty(name="Request transparency map")
    request_sss: bpy.props.BoolProperty(name="Request SSS map")
    
    def get_request_render_data(self):
        data = {}
        data['image_name'] = self.id_data.name
        data['resolution'] = self.id_data.size[0]
        maps = []
        # There should be a way to get a reference to the parameter, not just its value
        if self.request_albedo:
            maps.append("albedo")
        if self.request_roughness:
            maps.append("roughness")
        if self.request_metallicity:
            maps.append("metallicity")
        if self.request_normal:
            maps.append("normal")
        if self.request_occlusion:
            maps.append("occlusion")
        if self.request_emission:
            maps.append("emission")
        if self.request_depth:
            maps.append("depth")
        #if self.request_opacity:
        #    maps.append("transparency")
        if self.request_sss:
            maps.append("sss")
        data["maps"] = maps
        return data


def parameter_update(self, context):
        if self.should_update:
            data_to_send = {}
            data_to_send["command"] = "parameter_change"
            data_to_send["node_name"] = self.node_name
            data_to_send["param_name"] = self.param_name
            data_to_send["param_value"] = self.value
            data_to_send["parameter_type"] = "remote" if self.is_remote else "local" # TODO: Rename (e.g. "is the type int or is the type remote?")
            data_to_send["render"] = str(self.owner_image.mml_properties.auto_update)
            print("Data_to_send['render']: ", data_to_send['render'])

            image_rr_data = self.owner_image.mml_properties.get_request_render_data()
            for key in image_rr_data:
                data_to_send[key] = image_rr_data[key]
            print("data_to_send['render']: ", data_to_send['render'])
            mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))
         


class MMLParameters(bpy.types.PropertyGroup):
    node_name: bpy.props.StringProperty()
    param_name: bpy.props.StringProperty()
    param_label: bpy.props.StringProperty()
    value: bpy.props.StringProperty(update=parameter_update)
    owner_image: bpy.props.PointerProperty(type=bpy.types.Image)
    should_update: bpy.props.BoolProperty()
    is_remote: bpy.props.BoolProperty()
    
    def get_id(self):
        return self.param_label if self.owner_image.mml_properties.use_remote_parameters else "{}/{}".format(self.node_name, self.param_name)
    
    

class Island():
    def __init__(self, bm, uv_layer, loop):
        self.loops = self.find_uv_island_loops(loop, uv_layer)
        self.uv_boundary_loops = [loop for loop in self.loops if Island.is_loop_uv_boundary(loop, uv_layer)]


    def get_loops(self):
        return self.loops


    def get_vertices(self):
        output = set()
        for loop in self.loops:
            output.add(loop.vert)
        return output


    def get_inner_points(self):
        return self.inner_points


    def find_uv_island_loops(self, loop, uv_layer):
        stack = [loop]
        output = []
        while len(stack) > 0:
            current_loop = stack.pop()
            next_loop = current_loop.link_loop_next
            if next_loop not in output:
                stack.append(next_loop)
                output.append(next_loop)
            if Island.is_loop_uv_boundary(current_loop, uv_layer):
                continue
            for adjacent_loop in current_loop.link_loops:
                if not adjacent_loop in output:
                    stack.append(adjacent_loop)
                    output.append(adjacent_loop)
        return output

    
    def __repr__(self):
        return str([str(loop.vert.index) + "-" + str(loop.link_loop_next.vert.index) for loop in self.loops])


    def find_inner_points(self, uv_layer, size_factors):
        print("find_inner_points()")
        faces = set()
        for loop in self.loops:
            faces.add(loop.face)
        points = set()
        for face in faces:
            points = points.union(Island.find_face_points(face, uv_layer, size_factors))
        return points

    @classmethod
    def evaluate_loop_at_x(cls, loop, uv_layer, x):
        x1,y1 = loop[uv_layer].uv
        x2,y2 = loop.link_loop_next[uv_layer].uv
        return cls.evaluate_at_x(x1, x2, y1, y2, x)

    @classmethod
    def evaluate_resized_loop_at_x(cls, loop, uv_layer, x, resize_factors, offset=0.0):
        x1 = loop[uv_layer].uv.x * resize_factors[0]
        y1 = loop[uv_layer].uv.y * resize_factors[1]
        x2 = loop.link_loop_next[uv_layer].uv.x * resize_factors[0]
        y2 = loop.link_loop_next[uv_layer].uv.y * resize_factors[1]
        return cls.evaluate_at_x(x1,x2,y1,y2,x, offset)


    class VerticalLineException(Exception):
        pass


    @classmethod
    def evaluate_at_x(self, x1, x2, y1, y2, x, offset=0.0):
        if not min(x1,x2) - offset < x < max(x1,x2) + offset:
            return None
        if abs(x2-x1) < 0.001:
            raise Island.VerticalLineException()
        m = (y2-y1)/(x2-x1)
        return y1 + m * (x - x1)


    # This method is faster, but it causes rounding issues
    # @classmethod
    # def find_quad_inner_points(cls, p1, p2, p3, p4):    # I expect this to work with tris anyways
    #     v21 = p1 - p2
    #     v34 = p4 - p3 
    #     initial_points = [tuple([math.floor(value) for value in p]) for p in [p1,p2,p3,p4]]
    #     output = set( initial_points)
    #     point = initial_points[1]
    #     print("output: ", output)
    #     if abs(p3.x - p2.x) > 5:
    #         start_base_vector = p2 if p2.x < p3.x else p3
    #         end_base_vector = p2 if p2.x > p3.x else p3
    #         x_span = end_base_vector.x - start_base_vector.x
    #         for x in range(math.floor(start_base_vector.x), math.ceil(end_base_vector.x)):
    #             s = (math.floor(end_base_vector.x) - x) / x_span
    #             interpolated_base_vector = start_base_vector * s + end_base_vector * ( 1 - s)
    #             interpolated_side_vector = v21 * s + v34 * ( 1 - s )
    #             start_side_vector = interpolated_base_vector if interpolated_base_vector.y < (interpolated_base_vector + interpolated_side_vector).y else (interpolated_base_vector + interpolated_side_vector)
    #             end_side_vector = interpolated_base_vector if interpolated_base_vector.y > (interpolated_base_vector + interpolated_side_vector).y else (interpolated_base_vector + interpolated_side_vector)
    #             y_span = end_side_vector.y - start_side_vector.y
    #             for y in range(math.floor(start_side_vector.y), math.ceil(end_side_vector.y)):
    #                 t = (math.floor(end_side_vector.y) - y) / y_span
    #                 current_point = tuple(math.floor(value) for value in (start_side_vector * t + end_side_vector * ( 1 - t )))
    #                 if abs(current_point[0] - point[0]) + abs(current_point[1] - point[1]) > 1:
    #                     extra_point_1 = (math.floor(point[0]) + 1, math.floor(point[1]))
    #                     extra_point_2 = (math.floor(point[0]), math.floor(point[1]) + 1)
    #                     output.add( extra_point_1)
    #                     output.add( extra_point_2)
    #                 print("Adding point ", point)
    #                 point = current_point
    #                 output.add( point )
    #     print("find_quad_inner_points found:")
    #     print(output)
    #     return output


    @classmethod
    def find_face_points(cls, face, uv_layer, size_factors):
        return cls.find_loops_inner_points(face.loops, uv_layer, size_factors)


    @classmethod
    def find_loops_inner_points(cls, loops, uv_layer, size_factors, offset=4):
        min_x = max(0, math.floor( min( [size_factors[0] * loop[uv_layer].uv.x for loop in loops] ) - offset ))
        max_x = min(size_factors[0], math.ceil( max( [size_factors[0] * loop[uv_layer].uv.x for loop in loops] ) + offset ))
        min_y = max(0, math.floor( min( [size_factors[1] * loop[uv_layer].uv.y for loop in loops] ) - offset ))
        max_y = min(size_factors[1], math.ceil( max( [size_factors[1] * loop[uv_layer].uv.y for loop in loops] ) + offset ))

        points = [Vector((size_factors[0]*loop[uv_layer].uv.x, size_factors[1]*loop[uv_layer].uv.y)) for loop in loops]
        print(points)
        for loop in loops:
            if cls.is_loop_uv_boundary(loop, uv_layer):
                center = Vector((sum( [p.x for p in points] ), sum( [p.y for p in points]))) / len(points)
                for i in range(len(points)):
                    points[i] = points[i] + (points[i] - center).normalized() * 0.02 * size_factors[0]
                break

        output = set()
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                point = Vector((x,y))
                intersects = geo.intersect_point_quad_2d(point , points[0], points[1], points[2], points[3%len(points)])
                if intersects:
                    output.add( (x,y))
        return output


    @classmethod
    def is_loop_boundary(cls, loop):
        if not Island.are_vectors_equal(loop.vert.co, loop.link_loops[0].link_loop_next.vert.co):
            return False
        if not Island.are_vectors_equal(loop.link_loop_next.vert.co, loop.link_loops[0].vert.co):
            return False
        return True
    
    @classmethod
    def is_loop_uv_boundary(cls, loop, uv_layer):
        if len(loop.link_loops) == 0: # It's assumed that if it's a boundary loop, it's an uv boundary loop
            return True
        if not Island.are_vectors_equal(loop[uv_layer].uv, loop.link_loops[0].link_loop_next[uv_layer].uv):
            return False
        if not Island.are_vectors_equal(loop.link_loop_next[uv_layer].uv, loop.link_loops[0][uv_layer].uv):
            return False
        return True
    
    @classmethod
    def are_vectors_equal(cls, vec_a, vec_b):
        diff = vec_b - vec_a
        return max(diff) > 0.001 or -min(diff) > 0.001

    @classmethod
    def are_loops_uv_adjacent(cls, loop_a, loop_b, uv_layer):
        if cls.are_vectors_equal(loop_a[uv_layer].uv, loop_b[uv_layer].uv) and cls.are_vectors_equal(loop_a.link_loop_next[uv_layer].uv, loop_b.link_loop_next[uv_layer].uv):
            return True
        if cls.are_vectors_equal(loop_a[uv_layer].uv, loop_b.link_loop_next[uv_layer].uv) and cls.are_vectors_equal(loop_a.link_loop_next[uv_layer].uv, loop_b[uv_layer].uv):
            return True
        return False

    @classmethod
    def list_loops_vert_indices(cls, loops):
        return [str(loop.vert.index) + "-" + str(loop.link_loop_next.vert.index) for loop in loops]



class MML():
    command_key_requirements = {
        "pong" : [],
        "replace_image" : ["image_name", "image_data"], # TODO: Make use of image names for proper identification
        "init_parameters" : ["image_name", "parameters_type", "parameters"],
        "inform" : ["info"],
        "request_parameters": ["image_name"],
        "parameters_loaded": []
    }
    info_message = ""
    received_messages = []
    mm_parameters_loaded = False

    @classmethod
    def key_check(self, data):
        if "command" not in data:
            print("ERROR: \"command\" key not found in data")
            return False
        for key in self.command_key_requirements[data["command"]]:
            if key not in data:
                MML.inform("ERROR: key \"{}\" not found in data".format(key))
                return False
        return True
        
    @classmethod
    def interpret(self, data):
        if data[:5] == b"json|":
            self.interpret_json(data[5:]) 
        elif data[:6] == b"image|":
            padding = int(data[6:9])
            image_name = str(data[10:padding-6])[2:-1]
            size = int(data[padding-5:padding-1])
            self.replace_image(image_name, size, data[padding:]) # TODO: Do away with the unnecessary copying
        else:
            print("Failed to interpret message")
        return
    
    @classmethod
    def interpret_json(cls, data):
        data = json.loads(data)
        if not cls.key_check(data):
            MML.inform("Error: Key check fail")
            return
        command = data["command"]
        if command == "pong":
            #print("pong")
            pass
        elif command == "init_parameters":
            print("Initializing parameters ({})".format(data["parameters_type"]))
            MML.initialize_parameters(data)
        elif command == "inform":
            MML.inform(data["info"])
        elif command == "request_parameters":
            data_to_send = { "command":"set_multiple_parameters", "parameters":[], "image_name":data["image_name"] }
            img = bpy.data.images[data["image_name"]]
            for parameter in img.mml_remote_parameters:
                parameter_data = json.dumps({ "node_name":parameter.node_name, "param_name":parameter.param_name, "param_label":parameter.param_label, "param_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "param_type":"remote"})
                data_to_send["parameters"].append(parameter_data)
            for parameter in img.mml_local_parameters:
                parameter_data = json.dumps({ "node_name":parameter.node_name, "param_name":parameter.param_name, "param_label":"",  "param_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "param_type":"local"})
                data_to_send["parameters"].append(parameter_data)
                mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))
            print(data_to_send)
        elif command == "parameters_loaded":
            MML.mm_parameters_loaded = True

    @classmethod
    def replace_image(cls, image_name, size, data):
        if image_name in bpy.data.images:
            img = bpy.data.images[image_name]
        else:
            img = bpy.data.images.new(name=image_name, width=size, height=size)

        t0 = time.time()
        if img.mml_properties.island_only:            
            island_data = json.loads(img.mml_properties.island_data)
            points_to_island = island_data['points_to_island']

            # Made so as to work only with selected vertices' island at the time of receiving MML data.
            # Determined to be not worth having.
            # bm = bmesh.from_edit_mesh(bpy.context.object.data) # Is there a better way to retrieve this data?
            # bm = bmesh.from_edit_mesh(mml.)
            # uv_layer = bm.loops.layers.uv.active
            # selected_island_indices = set()
            # for vert in bm.verts:
            #     print("vert: ", vert)
            #     for loop in vert.link_loops:
            #         print("loop: ", loop)
            #         uv = loop[uv_layer] 
            #         point = tuple(math.floor(value*size) for value in loop[uv_layer].uv)
            #         print("point: ", point)
            #         if uv.select:
            #             print("uv is selected")
            #             #selected_island_indices.add( points_to_island[str(hash(point))] )
            #             try:
            #                 selected_island_indices.add( points_to_island[str(point)] )
            #                 print("Point added")
            #             except KeyError as e:
            #                 #MML.inform(f"Key for point at {point} (hash {hash(point)}) not found!")
            #                 MML.inform(f"Key for point at {point} not found!")
            #                 continue
            #                 #print("island_to_points:")
            #                 #print(island_data['island_to_points'])
            #                 #print("points_to_island:")
            #                 #print(points_to_island)
            #                 #return

            island_to_points = island_data['island_to_points']
            t1 = time.time()
            pixel_data = list(img.pixels[:])
            MML.inform(f"Pixel data copied in {time.time() - t1} seconds.")
            t1 = time.time()
            MML.inform("island_data.keys(): ", island_to_points.keys())
            for island_index in island_to_points.keys():
                points_list = island_to_points[str(island_index)]
                for point in points_list:
                    pixel_index = (size * point[1] + point[0]) * img.channels
                    for i in range(img.channels):
                        pixel_data[pixel_index+i] =  data[pixel_index+i] / 255.0
            MML.inform(f"Pixel data modified in {time.time() - t1} seconds.")
            t1 = time.time()
            img.pixels.foreach_set(pixel_data)
            MML.inform(f"Pixel data replaced in {time.time() - t1} seconds.")
        else:
            if len(img.pixels) != len(data):
                MML.inform("Warning: Expected data of size {}, got {}".format(len(img.pixels), len(data)))
                img.scale(size, size)
      
            img.pixels.foreach_set([byte / 255.0 for byte in data])
        t1 = time.time()
        img.pack()
        img.update()
        bpy.context.view_layer.update()
        bpy.context.scene.view_layers.update()
        MML.inform(f"Image replaced in {time.time() - t0:.2f} seconds.")

    @classmethod
    def initialize_parameters(cls, data):
        cls.inform("Initializing parameters.")
        img = bpy.data.images[data["image_name"]]
        parameters = None
        if data["parameters_type"] == "remote":
            print("\n Remote parameters: \n")
            parameters = img.mml_remote_parameters
        elif data["parameters_type"] == "local":
            print("\n Local: \n")
            parameters = img.mml_local_parameters
        else:
            cls.inform("ERROR: Incorrect parameters type on initialization.")
        parameters.clear()
        received_parameters_data = data["parameters"]

        for entry in received_parameters_data:
            print("entry['node']: ", entry['node'])
            new_parameter = parameters.add()
            new_parameter.owner_image = img
            new_parameter.node_name = entry['node']
            new_parameter.param_name = entry['param_name']
            new_parameter.should_update = False
            new_parameter.value = str(entry['param_value'])
            new_parameter.should_update = True
            new_parameter.param_label = entry['param_label']
        return
        
    @classmethod
    def is_ready(cls):
        return mml_client.MMLClient.instance.status == mml_client.Status.connected and MML.mm_parameters_loaded
    
    @classmethod
    def on_disconnect(cls):
        cls.mm_parameters_loaded = False
        
    @classmethod
    def inform(cls, message):
        cls.info_message = message
        print(message)
