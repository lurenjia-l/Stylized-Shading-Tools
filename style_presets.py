"""
风格化着色工具 · 扩展模块 (style_presets.py)
================================================
为 AI / 艺术家提供增强能力，不修改原插件任何现有行为：

1. node.apply_style_preset   — 一键套用风格配方（添加节点组 + 自动串联 + 设置参数）
2. node.query_group_params   — 打印/导出选中节点组的参数 schema（供 AI 调参前自省）
3. node.export_nodes_code    — 把选中节点/节点组导出为 Python 重建代码 + 结构说明
                               （节点作用、参数、连线关系，AI 可直接读懂结构与用途）

AI 通过 Blender MCP 的 execute_blender_code 调用示例：
    bpy.ops.node.apply_style_preset(preset='three_color')
    bpy.ops.node.query_group_params()
    bpy.ops.node.export_nodes_code()
"""

import bpy
import os
from bpy.types import Operator, Panel
from bpy.props import EnumProperty

from . import material_functions as mf

# ==================== 风格配方库 ====================
# groups: 需要添加并按顺序串联的散装组（或全能组）
# params: {组名: {参数名: 值}} —— 菜单参数用字符串，其余用数字/颜色(RGBA)
STYLE_PRESETS = {
    "base_toon": {
        "label": "基础卡通二分",
        "description": "主节点 + Smoother Step 二分光照，暖亮冷暗",
        "groups": ["主节点"],
        "params": {
            "主节点": {
                "过渡方式": "Smoother Step",
                "亮部范围": 0.5,
                "暗部范围": 0.45,
                "阶梯步数": 3,
                "亮部明度": 1.05,
                "暗部明度": 0.35,
                "亮部": (1.0, 0.93, 0.82, 1.0),
                "暗部": (0.22, 0.13, 0.22, 1.0),
            },
        },
    },
    "three_color": {
        "label": "经典三色卡通",
        "description": "主节点 + 面朝向(Facing)轮廓光（经典赛璐璐）",
        "groups": ["主节点", "轮廓光"],
        "params": {
            "主节点": {
                "过渡方式": "Smoother Step",
                "亮部范围": 0.55,
                "暗部范围": 0.42,
                "阶梯步数": 3,
                "亮部": (1.0, 0.96, 0.88, 1.0),
                "暗部": (0.18, 0.15, 0.3, 1.0),
            },
            "轮廓光": {
                "Layer Weight": "Facing",
                "Blend": 0.8,
                "范围": 0.25,
                "轮廓光颜色": (0.9, 0.62, 0.45, 1.0),
                "Blending Mode": "Mix",
            },
        },
    },
    "painterly": {
        "label": "手绘高光",
        "description": "主节点 + 柔和卡通高光",
        "groups": ["主节点", "高光"],
        "params": {
            "主节点": {
                "过渡方式": "Smoother Step",
                "亮部范围": 0.5,
                "暗部范围": 0.4,
                "亮部明度": 1.1,
                "暗部明度": 0.4,
            },
            "高光": {
                "高光开关": 1.0,
                "高光范围": 0.28,
                "软硬钳制:小值": 0.2,
                "软硬钳制:大值": 0.85,
                "高光染色": (1.0, 0.95, 0.9, 1.0),
            },
        },
    },
    "dirty_realistic": {
        "label": "脏旧写实",
        "description": "主节点 + 脏迹 + AO（做旧质感）",
        "groups": ["主节点", "脏迹", "AO"],
        "params": {
            "主节点": {
                "过渡方式": "Smoother Step",
                "亮部范围": 1.0,
                "暗部范围": 0.0,
                "暗部明度": 0.5,
            },
            "脏迹": {
                "强度": 0.9,
                "Menu": "fBM",
                "Scale": 5.0,
                "Roughness": 0.7,
                "脏迹色": (0.1, 0.08, 0.07, 1.0),
                "Blending Mode": "Multiply",
            },
            "AO": {
                "AO开关": 1.0,
                "Distance": 0.5,
                "范围": 0.8,
                "AO Color": "自身颜色",
                "明度": 0.35,
            },
        },
    },
    "depth_fog": {
        "label": "景深感",
        "description": "主节点 + Z轴深度渐变染色（近实远虚）",
        "groups": ["主节点", "Z轴变化"],
        "params": {
            "主节点": {
                "过渡方式": "Smoother Step",
                "亮部范围": 0.5,
                "暗部范围": 0.4,
            },
            "Z轴变化": {
                "Z轴变化开关": 1.0,
                "From Min": 0.5,
                "From Max": 1.0,
                "自身颜色/染色": 1,
                "Z轴颜色": (0.55, 0.62, 0.78, 1.0),
                "明度": 0.85,
                "影响系数": 0.8,
            },
        },
    },
}


# ==================== 辅助函数 ====================
def get_color_input(node):
    """在节点实例上找到用于串联的颜色输入端口（优先 Color/颜色/col/输入）"""
    if not node:
        return None
    for cand in ("Color", "颜色", "col", "输入"):
        if cand in node.inputs:
            return node.inputs[cand]
    for inp in node.inputs:
        if inp.type == "RGBA" and not inp.is_linked:
            return inp
    return None


def set_group_input(node, name, value):
    """按端口类型设置默认值；菜单用字符串。不存在的参数静默跳过。"""
    if name not in node.inputs:
        return False
    sock = node.inputs[name]
    try:
        if sock.type == "MENU":
            sock.default_value = str(value)
        elif sock.type == "INT":
            sock.default_value = int(value)
        elif sock.type == "FLOAT":
            sock.default_value = float(value)
        elif sock.type == "RGBA":
            sock.default_value = tuple(value)
        elif sock.type == "VECTOR":
            sock.default_value = tuple(value)
        else:
            sock.default_value = value
        return True
    except Exception:
        return False


def _base_of(name):
    """从节点/节点组名提取基础名（去掉 .001 后缀与 _副本后缀）"""
    return name.split(".")[0].split("_")[0]


def find_group_nodes(tree, base_names):
    """返回 {基础名: 组节点}，基础名 = 节点组名去掉 .001/副本后缀"""
    result = {}
    for node in tree.nodes:
        if node.type == "GROUP" and node.node_tree:
            base = None
            b1 = _base_of(node.name)
            b2 = _base_of(node.node_tree.name)
            if b1 in base_names:
                base = b1
            elif b2 in base_names:
                base = b2
            if base and base not in result:
                result[base] = node
    return result


def chain_group_nodes(tree, nodes_by_name, order):
    """按 order 顺序串联 Color 输出→下一组 Color 输入，返回最后一个节点"""
    links = tree.links
    prev = None
    for name in order:
        node = nodes_by_name.get(name)
        if node is None:
            continue
        if prev is not None:
            target = get_color_input(node)
            if target is not None and len(prev.outputs) > 0:
                if target.links:
                    links.remove(target.links[0])
                links.new(prev.outputs[0], target)
        prev = node
    return prev


def connect_to_material_output(tree, from_node):
    """把 from_node 的第一个输出接到材质输出 Surface（移除旧连线）"""
    output_node = None
    for node in tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
            break
    if output_node is None:
        output_node = tree.nodes.new(type="ShaderNodeOutputMaterial")
    surface = output_node.inputs.get("Surface")
    if surface is None:
        return
    if surface.links:
        tree.links.remove(surface.links[0])
    if from_node is not None and len(from_node.outputs) > 0:
        tree.links.new(from_node.outputs[0], surface)


def get_or_create_material(obj):
    if len(obj.data.materials) == 0:
        mat = bpy.data.materials.new(name=f"{obj.name}_材质")
        obj.data.materials.append(mat)
    else:
        mat = obj.active_material
        if mat is None:
            mat = obj.data.materials[0]
    mat.use_nodes = True
    return mat


def add_chained_groups_to_material(obj, groups, params):
    """为物体添加 groups（按 BULK_GROUPS 顺序）并串联、设参、连输出"""
    mat = get_or_create_material(obj)
    tree = mat.node_tree
    links = tree.links
    nodes = tree.nodes

    nodes_by_name = {}
    for group_name in groups:
        unique = mf.get_unique_group_for_material(group_name, obj, mat)
        if unique is None:
            continue
        group_node = nodes.new(type="ShaderNodeGroup")
        group_node.node_tree = unique
        group_node.name = group_name
        group_node.label = group_name
        group_node.location = (-2000 + len(nodes_by_name) * 300, 0)
        nodes_by_name[group_name] = group_node

    # 串联（按 BULK_GROUPS 定义的顺序；未知组按添加顺序排在后面）
    order = [g for g in mf.BULK_GROUPS if g in nodes_by_name]
    order += [g for g in nodes_by_name if g not in order]
    last = chain_group_nodes(tree, nodes_by_name, order)

    # 设置参数
    for group_name, p in params.items():
        node = nodes_by_name.get(group_name)
        if node is None:
            continue
        for k, v in p.items():
            set_group_input(node, k, v)

    # 连到材质输出
    if last is not None:
        connect_to_material_output(tree, last)
    return last is not None


# ==================== 操作符 ====================
class NODE_OT_apply_style_preset(Operator):
    """一键套用风格配方：添加节点组 + 自动串联 + 设置参数"""
    bl_idname = "node.apply_style_preset"
    bl_label = "套用风格配方"
    bl_description = "一键为选中物体套用风格配方（添加+串联+设参）"
    bl_options = {"REGISTER", "UNDO"}

    preset: EnumProperty(
        name="风格配方",
        items=[(k, v["label"], v.get("description", "")) for k, v in STYLE_PRESETS.items()],
    )

    def execute(self, context):
        selected = [o for o in context.selected_objects if o.type == "MESH"]
        if not selected:
            self.report({"WARNING"}, "请先选中一个或多个网格物体")
            return {"CANCELLED"}
        cfg = STYLE_PRESETS.get(self.preset)
        if cfg is None:
            self.report({"ERROR"}, f"未知配方: {self.preset}")
            return {"CANCELLED"}
        ok = 0
        for obj in selected:
            if add_chained_groups_to_material(obj, cfg["groups"], cfg["params"]):
                ok += 1
        self.report({"INFO"}, f"配方「{cfg['label']}」已套用到 {ok}/{len(selected)} 个物体")
        return {"FINISHED"}


class NODE_OT_query_group_params(Operator):
    """导出选中节点组的参数 schema 到文本文件与控制台（AI 自省用）"""
    bl_idname = "node.query_group_params"
    bl_label = "导出节点组参数"
    bl_description = "把选中节点组的输入参数（名称/类型/默认值/范围）写入文本文件"
    bl_options = {"REGISTER"}

    def execute(self, context):
        space = context.space_data
        tree = space.edit_tree if space and space.type == "NODE_EDITOR" else None
        selected = []
        if tree is not None:
            selected = [n for n in tree.nodes if n.select and n.type == "GROUP"]
        # 无节点编辑器或无选中时，回退到活动物体的活动材质树（便于 AI 在无编辑器环境下自省）
        if not selected:
            obj = context.active_object
            if obj and obj.type == "MESH" and obj.active_material and obj.active_material.use_nodes:
                tree = obj.active_material.node_tree
                selected = [n for n in tree.nodes if n.type == "GROUP"]
        if not selected:
            self.report({"WARNING"}, "请选中节点组，或选中一个有材质（含节点组）的物体")
            return {"CANCELLED"}

        lines = []
        for node in selected:
            base = node.node_tree.name.split(".")[0]
            lines.append(f"=== {node.name} (模板: {base}) ===")
            for inp in node.inputs:
                default = None
                try:
                    default = inp.default_value
                except Exception:
                    pass
                default_txt = ""
                if default is not None:
                    if isinstance(default, (float, int)):
                        default_txt = f" 默认={default:g}"
                    elif isinstance(default, str):
                        default_txt = f" 默认={default}"
                    elif hasattr(default, "__len__"):
                        default_txt = f" 默认={tuple(round(x, 3) for x in default)}"
                extra = ""
                if inp.type == "FLOAT":
                    try:
                        extra = f" 范围=[{inp.min_value:g},{inp.max_value:g}]"
                    except Exception:
                        pass
                lines.append(f"  IN  [{inp.name}] {inp.type}{default_txt}{extra}")
            for outp in node.outputs:
                lines.append(f"  OUT [{outp.name}] {outp.type}")

        text = "\n".join(lines)
        print(text)
        # 同时写入临时文件，方便 AI 通过文件工具读取
        dump_path = os.path.join(bpy.app.tempdir, "group_params_dump.txt")
        try:
            with open(dump_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.report({"INFO"}, f"参数已导出: {dump_path}")
        except Exception:
            self.report({"INFO"}, "参数已打印到控制台")
        return {"FINISHED"}


# ==================== 节点结构导出为代码（AI 可读） ====================
# 内置节点组的用途说明，帮助 AI 理解导出的结构在做什么
GROUP_DESCRIPTIONS = {
    "主节点": "核心二分光照：按亮度阈值(暗部范围~亮部范围)把 Shader to RGB 拆成亮部/暗部，分别 HSV 染色后按过渡方式混合",
    "轮廓光": "边缘光：Layer Weight(Facing/Fresnel) 生成边缘遮罩，把 轮廓光颜色 按 Blending Mode 叠到底色",
    "高光": "卡通高光：Specular BSDF + 软硬钳制遮罩，高光染色叠加，高光开关=1 显示",
    "反射": "Voronoi 反射图案（单色/多色）叠加到底色",
    "脏迹": "双噪声(fBM/Multifractal)脏迹遮罩，脏迹色 Multiply/混合到底色",
    "AO": "环境光遮蔽暗角：AO 节点 + 范围钳制，压暗或染色",
    "Z轴变化": "相机深度(View Z Depth)渐变：深度重映射为系数后做 HSV 染色/混合",
    "渐变": "控制器空物体驱动的色彩渐变（并入式叠加在原材质上）",
    "多功能风格化shader": "全能一站式风格化材质（光照+染色+高光+轮廓光+反射+脏迹+AO+Z轴变化 全部内置）",
    "原理化拓展光源": "灯光组(Lightgroup)驱动的 Principled BSDF 分层光照，灯光颜色 HSV/HSL 处理后叠加",
    "金属拓展光源": "灯光组驱动的 Metal BSDF 分层光照",
    "光泽拓展光源": "灯光组驱动的 Glossy BSDF 分层光照",
    "漫射拓展光源": "灯光组驱动的 Diffuse BSDF 分层光照",
    "混合颜色": "颜色混合工具（18 种 Blending Mode）",
    "映射范围": "数值重映射工具（Linear/Stepped/Smooth/Smoother Step）",
    "纹理坐标": "纹理坐标选择工具",
    "Z深度钳制": "相机深度钳制遮罩工具",
}


def _fmt_val(v):
    if isinstance(v, (float, int)):
        return f"{v:g}"
    if isinstance(v, str):
        return f"'{v}'"
    if hasattr(v, "__len__"):
        try:
            return "(" + ", ".join(str(round(x, 3)) if isinstance(x, float) else str(x) for x in v) + ")"
        except Exception:
            return str(v)
    return str(v)


def _mk_var(name, used):
    base = "n_" + "".join(c for c in name if c.isalnum() or c == "_")
    if not base or base == "n_":
        base = "n_node"
    if base in used:
        i = 1
        while f"{base}_{i}" in used:
            i += 1
        base = f"{base}_{i}"
    used.add(base)
    return base


class NODE_OT_export_nodes_code(Operator):
    """把选中节点/节点组的结构与连线导出为 Python 重建代码 + AI 可读说明"""
    bl_idname = "node.export_nodes_code"
    bl_label = "导出节点为代码"
    bl_description = "把选中节点的结构(类型/连线/组模板/参数)导出为 Python 代码与说明，AI 可直接读懂结构及其作用"
    bl_options = {"REGISTER"}

    def execute(self, context):
        space = context.space_data
        tree = space.edit_tree if space and space.type == "NODE_EDITOR" else None
        selected = []
        if tree is not None:
            selected = [n for n in tree.nodes if n.select]
        # 无节点编辑器或无选中时，回退到活动物体的活动材质树（便于 AI 在无编辑器环境下自省）
        if not selected:
            obj = context.active_object
            if obj and obj.type == "MESH" and obj.active_material and obj.active_material.use_nodes:
                tree = obj.active_material.node_tree
                selected = list(tree.nodes)
        if not selected:
            self.report({"WARNING"}, "请选中节点，或选中一个有材质（含节点）的物体")
            return {"CANCELLED"}

        text = self.build_code(tree, selected)
        print(text)
        dump_path = os.path.join(bpy.app.tempdir, "node_export_code.py")
        try:
            with open(dump_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.report({"INFO"}, f"代码已导出: {dump_path}")
        except Exception:
            self.report({"INFO"}, "代码已打印到控制台")
        return {"FINISHED"}

    def build_code(self, tree, nodes):
        sel = set(nodes)
        lines = []
        lines.append("# " + "=" * 70)
        lines.append(f"# 节点结构导出（AI 可读）— 所在树: {tree.name}，节点数: {len(nodes)}")
        lines.append("# " + "=" * 70)
        lines.append("")
        lines.append("# —— 1) 结构说明：每个节点是什么、做什么 ——")
        for n in nodes:
            if n.type == "GROUP" and n.node_tree:
                base = n.node_tree.name.split(".")[0].split("_")[0]
                desc = GROUP_DESCRIPTIONS.get(base, "自定义节点组")
                lines.append(f"# [{n.name}] 类型=GROUP 模板={n.node_tree.name}")
                lines.append(f"#    作用: {desc}")
            else:
                lines.append(f"# [{n.name}] 类型={n.type} 标签={n.label or '-'}")
            params = []
            for inp in n.inputs:
                if inp.is_linked or inp.type in ("SHADER", "CLOSURE"):
                    continue
                try:
                    d = inp.default_value
                except Exception:
                    continue
                is_interesting = False
                if isinstance(d, (float, int)):
                    is_interesting = abs(d) > 1e-5
                elif isinstance(d, str):
                    is_interesting = True
                elif hasattr(d, "__len__"):
                    is_interesting = any(abs(x) > 1e-5 for x in d)
                if is_interesting:
                    params.append(f"{inp.name}={_fmt_val(d)}")
            if params:
                lines.append(f"#    参数: {', '.join(params)}")
        lines.append("")
        lines.append("# —— 2) 连线关系 ——")
        has_link = False
        for link in tree.links:
            if link.from_node in sel and link.to_node in sel:
                has_link = True
                lines.append(f"#   {link.from_node.name}.{link.from_socket.name} -> {link.to_node.name}.{link.to_socket.name}")
        if not has_link:
            lines.append("#   （选中节点之间没有连线）")
        lines.append("")
        lines.append("# " + "=" * 70)
        lines.append("# —— 3) 重建代码（粘贴到 Blender 的 Python 控制台可重建本结构） ——")
        lines.append("# " + "=" * 70)
        # 确定树引用
        mat = next((m for m in bpy.data.materials if m.node_tree == tree), None)
        if mat is not None:
            tree_ref = f"bpy.data.materials[{mat.name!r}].node_tree"
        else:
            w = next((w for w in bpy.data.worlds if w.node_tree == tree), None)
            tree_ref = f"bpy.data.worlds[{w.name!r}].node_tree" if w is not None else f"bpy.data.node_groups[{tree.name!r}]"
        lines.append("import bpy")
        lines.append(f"tree = {tree_ref}  # 若目标树不同，改成你的材质/节点组")
        lines.append("")
        used = set()
        created = {}
        for n in nodes:
            vname = _mk_var(n.name, used)
            created[n] = vname
            lines.append(f"{vname} = tree.nodes.new(type={n.type!r})")
            lines.append(f"{vname}.name = {n.name!r}")
            if n.label:
                lines.append(f"{vname}.label = {n.label!r}")
            lines.append(f"{vname}.location = ({n.location.x:.0f}, {n.location.y:.0f})")
            if n.type == "GROUP" and n.node_tree:
                lines.append(f"{vname}.node_tree = bpy.data.node_groups[{n.node_tree.name!r}]")
            for prop in ("blend_type", "operation", "interpolation_type"):
                if hasattr(n, prop):
                    try:
                        v = getattr(n, prop)
                        if isinstance(v, str):
                            lines.append(f"{vname}.{prop} = {v!r}")
                    except Exception:
                        pass
            for i, inp in enumerate(n.inputs):
                if inp.is_linked or inp.type in ("SHADER", "CLOSURE"):
                    continue
                try:
                    d = inp.default_value
                except Exception:
                    continue
                is_interesting = False
                if isinstance(d, (float, int)):
                    is_interesting = abs(d) > 1e-5
                elif isinstance(d, str):
                    is_interesting = True
                elif hasattr(d, "__len__"):
                    is_interesting = any(abs(x) > 1e-5 for x in d)
                if is_interesting:
                    lines.append(f"{vname}.inputs[{i}].default_value = {_fmt_val(d)}  # {inp.name}")
            lines.append("")
        if has_link:
            lines.append("# 连线")
            for link in tree.links:
                if link.from_node in sel and link.to_node in sel:
                    f_i = list(link.from_node.outputs).index(link.from_socket)
                    t_i = list(link.to_node.inputs).index(link.to_socket)
                    lines.append(f"tree.links.new({created[link.from_node]}.outputs[{f_i}], {created[link.to_node]}.inputs[{t_i}])  # {link.from_socket.name} -> {link.to_socket.name}")
        return "\n".join(lines)


# ==================== 面板 ====================
class VIEW3D_PT_style_presets(Panel):
    bl_label = "风格配方"
    bl_idname = "VIEW3D_PT_style_presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "风格化材质"
    bl_parent_id = "VIEW3D_PT_custom_nodes"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="一键套用配方", icon="PRESET")
        row = box.row(align=True)
        row.prop(context.scene, "style_preset_selector", text="配方")
        op = row.operator("node.apply_style_preset", text="应用", icon="PLAY")
        # 关键：把下拉框当前选中的配方显式传给操作符（否则按钮每次都套用默认第一个配方）
        op.preset = context.scene.style_preset_selector
        layout.separator(factor=0.5)
        layout.operator("node.export_nodes_code", text="导出节点为代码(AI可读)", icon="CONSOLE")


def get_preset_items(self, context):
    return [(k, v["label"], v.get("description", "")) for k, v in STYLE_PRESETS.items()]


def register_scene_properties():
    bpy.types.Scene.style_preset_selector = EnumProperty(
        name="风格配方",
        items=get_preset_items,
        description="要一键套用的风格配方",
    )


def unregister_scene_properties():
    if hasattr(bpy.types.Scene, "style_preset_selector"):
        del bpy.types.Scene.style_preset_selector


# ==================== 类列表 ====================
classes = [
    NODE_OT_apply_style_preset,
    NODE_OT_query_group_params,
    NODE_OT_export_nodes_code,
    VIEW3D_PT_style_presets,
]
