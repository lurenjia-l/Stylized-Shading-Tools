"""
材质功能模块
包含节点组加载、材质添加、风格化节点操作符等功能
"""

import bpy
import os
import random
from bpy.types import Panel, Menu, Operator
from bpy.props import StringProperty

# ==================== 配置区域 ====================
NODES_BLEND_PATH = os.path.join(os.path.dirname(__file__), "shader file", "my shader.blend")
NODE_GROUP_NAME = "多功能风格化shader"

# 散装节点组列表（已更新）：
# - 移除了"光照系数"（已删除）
# - 将"亮暗颜色"改名为"主节点"
BULK_GROUPS = [
    "主节点",  # 原"亮暗颜色"
    "轮廓光",
    "高光",
    "反射",
    "脏迹",
    "AO",
    "Z轴变化",
]
GRADIENT_NODES = [
    "渐变",        # 显示名, 实际节点组名
    "纹理坐标"
    "混合颜色"
    "映射范围"
    "Z深度钳制"
]

GRADIENT_GROUP_NAME = "渐变"
TEXCOORD_NODE_NAME = "Texture Coordinate.002"
FEEDBACK_URL = "https://b23.tv/hLvRt75"
MATERIAL_SUFFIX = "_Material"

# 光源拓展 BSDF 节点组列表（Shift+A → 风格化节点 → 光源拓展BSDF）
LIGHT_EXTENDED_GROUPS = [
    "原理化拓展光源",
    "金属拓展光源",
    "光泽拓展光源",
    "漫射拓展光源",
]


# ==================== 节点组加载与复制辅助函数 ====================
def ensure_node_group_loaded(group_name):
    """
    确保插件所需的节点组已正确加载到当前文件。
    如果当前文件中已存在同名节点组，则将其重命名为备份（添加 _old 后缀），
    然后从外部 .blend 文件强制加载全新的节点组。
    这样保证后续创建的副本使用正确的模板。
    """
    # 如果存在同名节点组，先备份
    existing = bpy.data.node_groups.get(group_name)
    if existing is not None:
        backup_name = f"{group_name}_old"
        counter = 1
        while backup_name in bpy.data.node_groups:
            backup_name = f"{group_name}_old_{counter:03d}"
            counter += 1
        existing.name = backup_name
        print(f"已将现有节点组 '{group_name}' 备份为 '{backup_name}'")

    # 从外部文件加载
    if not os.path.exists(NODES_BLEND_PATH):
        print(f"节点文件不存在: {NODES_BLEND_PATH}")
        return False

    with bpy.data.libraries.load(NODES_BLEND_PATH, link=False) as (data_from, data_to):
        if group_name not in data_from.node_groups:
            print(f"节点组 '{group_name}' 不存在于文件 {NODES_BLEND_PATH} 中")
            return False
        data_to.node_groups = [group_name]

    # 验证加载结果
    if group_name in bpy.data.node_groups:
        print(f"已从 {NODES_BLEND_PATH} 加载节点组: {group_name}")
        return True
    else:
        print(f"加载节点组 '{group_name}' 失败")
        return False


def copy_node_group_unique(base_group_name, custom_suffix=""):
    """
    创建节点组的独立副本，返回副本节点组。
    若 base_group_name 不存在，则尝试从外部文件加载（强制加载正确模板）。
    custom_suffix 用于区分不同使用场景（物体名/材质名/树名）
    """
    # 确保原始节点组存在（如果存在但可能是旧版本，也会被备份并重新加载）
    if not ensure_node_group_loaded(base_group_name):
        return None

    orig_group = bpy.data.node_groups[base_group_name]
    # 生成唯一新名称
    if custom_suffix:
        new_name = f"{base_group_name}_{custom_suffix}"
    else:
        new_name = f"{base_group_name}_copy"
    # 处理重名
    final_name = new_name
    counter = 1
    while final_name in bpy.data.node_groups:
        final_name = f"{new_name}_{counter:03d}"
        counter += 1

    # 复制节点组
    new_group = orig_group.copy()
    new_group.name = final_name
    print(f"已创建节点组: {final_name}")
    return new_group


def get_unique_group_for_material(base_group_name, obj, material):
    """为特定物体的材质生成独立节点组副本，返回节点组"""
    suffix = f"{obj.name}_{material.name}"
    # 限制名称长度，避免过长
    if len(suffix) > 50:
        suffix = suffix[:50] + str(random.randint(10, 99))
    return copy_node_group_unique(base_group_name, suffix)


def get_unique_group_for_node_tree(base_group_name, node_tree):
    """为节点编辑器中的特定节点树生成独立副本"""
    suffix = f"{node_tree.name}"
    if len(suffix) > 50:
        suffix = suffix[:50]
    return copy_node_group_unique(base_group_name, suffix)


# ==================== 材质添加函数 ====================
def add_node_group_to_material(obj, group_name):
    """为物体材质添加节点组实例（独立副本）并连接到材质输出"""
    if obj.type != 'MESH':
        return "物体不是网格物体，无法添加材质"

    if len(obj.data.materials) == 0:
        mat = bpy.data.materials.new(name=f"{obj.name}_材质")
        obj.data.materials.append(mat)
    else:
        mat = obj.active_material
        if mat is None:
            mat = obj.data.materials[0]

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # 获取输出节点
    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
            break
    if output_node is None:
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)

    # 创建独立节点组副本
    node_group = get_unique_group_for_material(group_name, obj, mat)
    if node_group is None:
        return f"无法创建节点组 '{group_name}' 的独立副本"

    group_node = nodes.new(type='ShaderNodeGroup')
    group_node.node_tree = node_group
    group_node.location = (0, 0)

    if len(group_node.outputs) > 0:
        surface_input = output_node.inputs['Surface']
        if surface_input.links:
            links.remove(surface_input.links[0])
        links.new(group_node.outputs[0], surface_input)
    else:
        return "节点组没有输出，请手动连接"

    return f"已为物体 {obj.name} 一键添加节点组"


def add_gradient_group_to_material(obj, context):
    """为物体添加渐变节点组，创建球形控制器空物体，并入式连接原材质网络"""
    if obj.type != 'MESH':
        return f"物体 {obj.name} 不是网格，跳过"

    # 创建独立副本（基于原始渐变组）
    node_group = copy_node_group_unique(GRADIENT_GROUP_NAME, f"{obj.name}_Gradient")
    if node_group is None:
        return f"无法加载渐变节点组 '{GRADIENT_GROUP_NAME}'"
    group_name = node_group.name

    if len(obj.data.materials) == 0:
        mat = bpy.data.materials.new(name=f"{obj.name}_材质")
        obj.data.materials.append(mat)
    else:
        mat = obj.active_material
        if mat is None:
            mat = obj.data.materials[0]
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
            break
    if output_node is None:
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (400, 0)

    original_surface_link = None
    if output_node.inputs['Surface'].links:
        original_surface_link = output_node.inputs['Surface'].links[0].from_socket

    group_node = nodes.new(type='ShaderNodeGroup')
    group_node.node_tree = node_group
    group_node.location = (0, 0)
    group_node.name = group_name
    group_node.label = group_name

    if original_surface_link and len(group_node.inputs) > 0:
        if output_node.inputs['Surface'].links:
            links.remove(output_node.inputs['Surface'].links[0])

        target_input = None
        for inp in group_node.inputs:
            if inp.name.lower() in ('color', '颜色', 'col'):
                target_input = inp
                break
        if target_input is None and len(group_node.inputs) > 0:
            target_input = group_node.inputs[0]
        if target_input:
            if target_input.links:
                links.remove(target_input.links[0])
            links.new(original_surface_link, target_input)

        if len(group_node.outputs) > 0:
            links.new(group_node.outputs[0], output_node.inputs['Surface'])
    else:
        if len(group_node.outputs) > 0:
            if output_node.inputs['Surface'].links:
                links.remove(output_node.inputs['Surface'].links[0])
            links.new(group_node.outputs[0], output_node.inputs['Surface'])

    empty_name = f"{obj.name}_控制器"
    existing_empty = bpy.data.objects.get(empty_name)
    if existing_empty:
        bpy.data.objects.remove(existing_empty, do_unlink=True)

    empty = bpy.data.objects.new(empty_name, None)
    empty.empty_display_type = 'SPHERE'
    empty.empty_display_size = 1.6
    empty.location = (0, 0, 0)
    context.scene.collection.objects.link(empty)
    empty.parent = obj
    for collection in obj.users_collection:
        if empty.name not in collection.objects:
            collection.objects.link(empty)

    texcoord_node = node_group.nodes.get(TEXCOORD_NODE_NAME)
    if texcoord_node and texcoord_node.type == 'TEX_COORD':
        texcoord_node.object = empty
    else:
        print(f"警告：在节点组 {group_name} 中未找到名为 {TEXCOORD_NODE_NAME} 的纹理坐标节点")

    return f"已为物体 {obj.name} 添加渐变节点组及控制器（并入式连接）"


# ==================== 操作符 ====================
class NODE_OT_add_gradient_group(Operator):
    """为选中物体添加色彩渐变节点组，并创建球形控制器空物体（独立副本）"""
    bl_idname = "node.add_gradient_group"
    bl_label = "添加色彩渐变节点"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "请先选中一个或多个网格物体")
            return {'CANCELLED'}

        success_count = 0
        last_controller = None
        for obj in selected_objects:
            result = add_gradient_group_to_material(obj, context)
            if result.startswith("已为"):
                success_count += 1
                last_controller = bpy.data.objects.get(f"{obj.name}_控制器")
            else:
                self.report({'WARNING'}, result)

        if last_controller:
            bpy.ops.object.select_all(action='DESELECT')
            last_controller.select_set(True)
            context.view_layer.objects.active = last_controller
            self.report({'INFO'}, f"成功为 {success_count} 个物体添加渐变节点组，已选中控制器")
        else:
            self.report({'INFO'}, f"成功为 {success_count} 个物体添加渐变节点组")
        return {'FINISHED'}


class NODE_OT_add_custom_group(Operator):
    """添加自定义节点组（在节点编辑器或为选中物体添加）"""
    bl_idname = "node.style_add_custom_group"
    bl_label = "添加风格化节点组"
    bl_options = {'REGISTER', 'UNDO'}

    group_name: StringProperty(
        name="节点组名称",
        default=NODE_GROUP_NAME,
        description="要添加的节点组名称"
    )

    def execute(self, context):
        space = context.space_data
        # 节点编辑器环境
        if space and space.type == 'NODE_EDITOR' and space.edit_tree:
            tree = space.edit_tree
            # 创建独立副本
            node_group = get_unique_group_for_node_tree(self.group_name, tree)
            if node_group is None:
                self.report({'ERROR'}, f"无法创建节点组 '{self.group_name}' 的独立副本")
                return {'CANCELLED'}

            for node in tree.nodes:
                node.select = False
            new_node = tree.nodes.new('ShaderNodeGroup')
            new_node.node_tree = node_group
            new_node.location = space.cursor_location
            new_node.select = True
            tree.nodes.active = new_node
            self.report({'INFO'}, f"已添加节点组到当前节点树")
            return {'FINISHED'}

        # 物体模式：为选中物体添加
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "请先选中一个物体")
            return {'CANCELLED'}

        success_count = 0
        for obj in selected_objects:
            result = add_node_group_to_material(obj, self.group_name)
            if result.startswith("已为"):
                success_count += 1
            else:
                self.report({'WARNING'}, result)

        self.report({'INFO'}, f"成功为 {success_count} 个物体添加节点组")
        return {'FINISHED'}


class NODE_OT_add_bulk_groups(Operator):
    """一键添加所有散装节点组（独立副本），并自动连接主节点→材质输出"""
    bl_idname = "node.add_bulk_groups"
    bl_label = "一键添加散装节点组"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 确保原始节点组都存在（会强制从插件文件加载）
        for group_name in BULK_GROUPS:
            if not ensure_node_group_loaded(group_name):
                self.report({'ERROR'}, f"无法加载节点组 '{group_name}'")
                return {'CANCELLED'}

        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "请先选中一个物体")
            return {'CANCELLED'}

        success_count = 0
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue

            if len(obj.data.materials) == 0:
                mat = bpy.data.materials.new(name=f"{obj.name}_材质")
                obj.data.materials.append(mat)
            else:
                mat = obj.active_material
                if mat is None:
                    mat = obj.data.materials[0]

            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            x_start = -2000
            y_start = 0
            spacing_x = 300
            main_node = None  # 替代原来的 light_color_node

            for i, group_name in enumerate(BULK_GROUPS):
                # 为每个物体、每个散装组创建独立副本
                unique_group = get_unique_group_for_material(group_name, obj, mat)
                if unique_group is None:
                    self.report({'WARNING'}, f"无法创建节点组 '{group_name}' 的独立副本，跳过")
                    continue
                group_node = nodes.new(type='ShaderNodeGroup')
                group_node.node_tree = unique_group
                group_node.location = (x_start + i * spacing_x, y_start)
                group_node.name = group_name
                group_node.label = group_name

                if group_name == "主节点":
                    main_node = group_node

            if main_node is None:
                self.report({'WARNING'}, f"物体 {obj.name} 缺少主节点，无法自动连接")
                success_count += 1
                continue

            # 获取或创建材质输出节点
            output_node = None
            for node in nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    output_node = node
                    break
            if output_node is None:
                output_node = nodes.new(type='ShaderNodeOutputMaterial')
                output_node.location = (x_start + len(BULK_GROUPS) * spacing_x, y_start)

            # 连接主节点到材质输出
            if len(main_node.outputs) > 0:
                surface_input = output_node.inputs.get('Surface')
                if surface_input is not None:
                    if surface_input.links:
                        links.remove(surface_input.links[0])
                    links.new(main_node.outputs[0], surface_input)

            success_count += 1

        self.report({'INFO'}, f"成功为 {success_count} 个物体添加散装节点组并自动连接")
        return {'FINISHED'}


# ==================== 节点编辑器菜单 ====================
class NODE_MT_bulk_nodes(Menu):
    bl_label = "基础风格化节点组"
    bl_idname = "NODE_MT_bulk_nodes"

    def draw(self, context):
        layout = self.layout
        for group_name in BULK_GROUPS:
            op = layout.operator("node.style_add_custom_group", text=group_name)
            op.group_name = group_name


class NODE_MT_gradient_node(Menu):
    bl_label = "辅助节点组"
    bl_idname = "NODE_MT_gradient_node"

    def draw(self, context):
        layout = self.layout
        op1 = layout.operator("node.style_add_custom_group", text=GRADIENT_GROUP_NAME)
        op1.group_name = GRADIENT_GROUP_NAME
        op2 = layout.operator("node.style_add_custom_group", text="纹理坐标")
        op2.group_name = "纹理坐标"
        op3 = layout.operator("node.style_add_custom_group", text="混合颜色")
        op3.group_name = "混合颜色"
        op4 = layout.operator("node.style_add_custom_group", text="映射范围")
        op4.group_name = "映射范围"
        op5 = layout.operator("node.style_add_custom_group", text="Z深度钳制")
        op5.group_name = "Z深度钳制"

class NODE_MT_light_extended(Menu):
    bl_label = "光源拓展BSDF"
    bl_idname = "NODE_MT_light_extended"

    def draw(self, context):
        layout = self.layout
        for group_name in LIGHT_EXTENDED_GROUPS:
            op = layout.operator("node.style_add_custom_group", text=group_name)
            op.group_name = group_name

class NODE_MT_custom_nodes(Menu):
    bl_label = "风格化节点"
    bl_idname = "NODE_MT_custom_nodes"

    def draw(self, context):
        layout = self.layout
        op = layout.operator("node.style_add_custom_group", text=NODE_GROUP_NAME)
        op.group_name = NODE_GROUP_NAME
        layout.menu(NODE_MT_bulk_nodes.bl_idname)
        layout.menu(NODE_MT_gradient_node.bl_idname)
        layout.menu(NODE_MT_light_extended.bl_idname)


def menu_func(self, context):
    self.layout.menu(NODE_MT_custom_nodes.bl_idname)


# ==================== 3D视图侧边栏面板 ====================
class VIEW3D_PT_custom_nodes(Panel):
    bl_label = "风格化材质工具"
    bl_idname = "VIEW3D_PT_custom_nodes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "风格化材质"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("wm.url_open", text="问题反馈请联系 https://b23.tv/hLvRt75", icon='URL').url = FEEDBACK_URL


class VIEW3D_PT_material_edit(Panel):
    bl_label = "材质编辑"
    bl_idname = "VIEW3D_PT_material_edit"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "风格化材质"
    bl_parent_id = "VIEW3D_PT_custom_nodes"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        op = layout.operator("node.style_add_custom_group", text="一键添加多功能风格化shader", icon='NODETREE')
        op.group_name = NODE_GROUP_NAME
        layout.separator()
        layout.operator("node.add_bulk_groups", text="一键添加散装风格化节点组", icon='NODETREE')
        layout.separator()
        layout.operator("node.add_gradient_group", text="添加色彩渐变节点", icon='NODE_TEXTURE')


# ==================== 类列表 ====================
classes = [
    NODE_OT_add_custom_group,
    NODE_OT_add_bulk_groups,
    NODE_OT_add_gradient_group,
    NODE_MT_bulk_nodes,
    NODE_MT_gradient_node,
    NODE_MT_light_extended,
    NODE_MT_custom_nodes,
    VIEW3D_PT_custom_nodes,
    VIEW3D_PT_material_edit,
]