# 风格化着色工具 / Stylized Shading Tools

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **简体中文** 👉 [点此跳转](#中文)

---

## English / 英文

### Description

**Stylized Shading Tools** is a Blender addon designed for NPR (Non-Photorealistic Rendering) workflows. It provides one-click node group creation, node repair tools, and practical utilities to speed up your stylized shading process.

 <img width="3840" height="2160" alt="大溪沟" src="https://github.com/user-attachments/assets/7beb886a-80bc-4b40-91d7-b10f15a696c6" />



### Features

- **One-click Material Creation**: Quickly add "Multi-function Stylized Shader", "Color Gradient Nodes", or a full set of modular node groups (Main Node, Rim Light, Specular, Reflection, Dirt, AO, Z-change, etc.).
 <img width="1512" height="996" alt="image" src="https://github.com/user-attachments/assets/68f28edb-9413-4246-b17e-20ff0933e7cc" />
"Color Gradient Nodes"：

 <img width="960" height="540" alt="npr" src="https://github.com/user-attachments/assets/ed4d08b2-e41d-4d16-87bd-0cd09179dc89" />

- **Node Repair Tool**: Automatically fix broken node groups like Surface Curvature, Cavity, Kuwahara, etc.

 <img width="960" height="540" alt="npr6" src="https://github.com/user-attachments/assets/438f86da-4595-4f28-b9f7-4a486e0c1262" />

- **Utility Tools**:
  - Empty object organizer (move child/parent empties to collections)

 <img width="960" height="540" alt="npr2" src="https://github.com/user-attachments/assets/601ddc46-a509-496e-8f2b-3b3169009f02" />
  
  - Batch rename (material ↔ object, collection objects with serial numbers)

 <img width="960" height="540" alt="npr3" src="https://github.com/user-attachments/assets/fa8fdcb1-3077-448d-bcf2-218b30f3241e" />
  
 <img width="960" height="540" alt="npr5" src="https://github.com/user-attachments/assets/f0951841-2e02-4070-98ae-fbd007c437d5" />

### Installation

1. Download the ZIP file from this repository (Code → Download ZIP).
2. Open Blender, go to `Edit` → `Preferences` → `Add-ons`.
3. Click `Install…`, select the downloaded ZIP file.
4. Find **"风格化着色工具"** in the list and check the box to enable it.
5. In the 3D View sidebar (press N), find the "风格化材质" tab to access all tools.

### Requirements

- Blender 3.4 or higher
- The plugin requires two .blend resource files (`shader file/my shader.blend` and `fix_node/fix_node.blend`). Make sure the directory structure remains intact after unzipping.

### The English text is automatically translated from Chinese. Some expressions may not be entirely accurate.

### License

This project is licensed under the **GPL-3.0 License**.

---

## 中文 / Chinese

### 插件简介

**风格化着色工具** 是一款专为 NPR（非真实感渲染）工作流设计的 Blender 插件，可快速添加风格化材质节点组、修复损坏节点，并提供实用工具集。

 <img width="3840" height="2160" alt="大溪沟" src="https://github.com/user-attachments/assets/783d9e0c-376c-4a96-89b6-eeec42589dd1" />

### 主要功能

- **一键添加材质**：快速添加"多功能风格化shader"、"色彩渐变节点"或全套散装节点组（主节点、轮廓光、高光、反射、脏迹、AO、Z轴变化等）。

 <img width="1512" height="996" alt="image" src="https://github.com/user-attachments/assets/c05a673e-ca0a-4b34-be43-5bdc267ab87c" />


"色彩渐变节点"：
<img width="960" height="540" alt="npr" src="https://github.com/user-attachments/assets/ed4d08b2-e41d-4d16-87bd-0cd09179dc89" />


- **节点修复工具**：自动修复 Surface Curvature、Cavity、Kuwahara 等损坏节点。

 <img width="960" height="540" alt="npr6" src="https://github.com/user-attachments/assets/438f86da-4595-4f28-b9f7-4a486e0c1262" />


- **实用工具集**：
  - 空物体整理（子级/父级空物体移动到集合）

 <img width="960" height="540" alt="npr2" src="https://github.com/user-attachments/assets/601ddc46-a509-496e-8f2b-3b3169009f02" />

  - 批量重命名（材质 ↔ 物体、集合内对象按序号重命名）

 <img width="960" height="540" alt="npr3" src="https://github.com/user-attachments/assets/fa8fdcb1-3077-448d-bcf2-218b30f3241e" />

 <img width="960" height="540" alt="npr5" src="https://github.com/user-attachments/assets/f0951841-2e02-4070-98ae-fbd007c437d5" />

### 安装方法

1. 下载本仓库的 ZIP 压缩包（点击绿色的 `Code` → `Download ZIP`）。
2. 打开 Blender，进入 `编辑` → `偏好设置` → `插件`。
3. 点击 `安装…`，选择下载的 ZIP 文件。
4. 在插件列表中找到 **“风格化着色工具”**，勾选启用。
5. 在 3D 视图侧边栏（按 N 键）中，找到 `风格化材质` 标签页，即可使用所有功能。

### 兼容要求

- Blender 3.4 或更高版本
- 插件需附带两个 .blend 资源文件（`shader file/my shader.blend` 和 `fix_node/fix_node.blend`），解压后请保持目录结构完整。

### 开源许可

本项目采用 **MIT 许可证**。
