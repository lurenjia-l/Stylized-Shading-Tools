bl_info = {
    "name": "风格化着色工具",
    "author": "路人甲",
    "version": (5, 0, 1),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar & Node Editor > Shift+A",
    "description": "一键为选中物体添加自定义风格化渲染材质节点组，以及一点别的功能",
    "category": "Node",
    "doc_url": "https://b23.tv/hLvRt75",
    "tracker_url": "https://b23.tv/hLvRt75",
}

import bpy

# 导入功能模块
from . import material_functions
from . import utility_functions
from . import node_fixer
from . import style_presets


# ==================== 注册 ====================
classes = (
    material_functions.classes
    + utility_functions.classes
    + node_fixer.classes
    + style_presets.classes
)


def register():
    # 注册所有类
    for cls in classes:
        bpy.utils.register_class(cls)
    # 注册场景扩展属性（用于集合重命名等）
    utility_functions.register_scene_properties()
    # 注册 AI 风格配方场景属性
    style_presets.register_scene_properties()
    # 追加菜单
    bpy.types.NODE_MT_add.append(material_functions.menu_func)

def unregister():
    bpy.types.NODE_MT_add.remove(material_functions.menu_func)
    # 注销场景属性
    utility_functions.unregister_scene_properties()
    style_presets.unregister_scene_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
