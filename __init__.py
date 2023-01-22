bl_info = {
    "name": "Material Maker Linker",
    "author": "Crunchsoft",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "location": "ImageEditor > Sidebar > MML",
    "description": "Link between Material Maker's ptex materials and Blender's image editor.",
    "warning": "",
    "category": "Paint",
}

if "bpy" in locals():
    import importlib
    importlib.reload(ui_mml)
    importlib.reload(mml_main)
    importlib.reload(mml_client)   
else:
    import bpy
    from . import ui_mml
    from . import mml_main as mml
    from . import mml_client

def register():
    bpy.utils.register_class(mml.MMLProperties)
    bpy.utils.register_class(mml.MMLParameters)
    bpy.utils.register_class(ui_mml.MMLPanel)
    bpy.types.Image.mml_remote_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters)
    bpy.types.Image.mml_local_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters) # A local parameter is one from a non-remote node
    bpy.types.Image.mml_properties = bpy.props.PointerProperty(type=mml.MMLProperties, name="MML Properties", description="MML properties")
    bpy.utils.register_class(mml_sender.MMLSubmit)
    bpy.utils.register_class(mml_sender.MMLRequestRender)
    bpy.utils.register_class(mml_client.OBJECT_OT_connect)
    bpy.utils.register_class(ui_mml.UI_UL_ParamsList)
    bpy.types.Image.params_list_index = bpy.props.IntProperty(name = "Index for ParamList",
                                             default = 0)

def unregister():
    bpy.utils.unregister_class(mml.MMLParameters)
    bpy.utils.unregister_class(mml.MMLProperties)
    bpy.utils.unregister_class(ui_mml.MMLPanel)
    del bpy.types.Image.mml_remote_parameters
    del bpy.types.Image.mml_local_parameters
    del bpy.types.Image.mml_properties
    del mml_sender.OJBECT_OT_send.mml_properties
    bpy.utils.unregister_class(mml_sender.MMLSubmit)
    bpy.utils.unregister_class(mml_sender.MMLRequestRender)
    bpy.utils.unregister_class(mml_client.OBJECT_OT_connect)
    bpy.utils.unregister_class(ui_mml.UI_UL_ParamsList)

    
if __name__ == '__main__':
        register()

