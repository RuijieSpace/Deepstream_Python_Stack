# Deepstream_Python_Stack

<div align="center">

![DeepStream](https://img.shields.io/badge/DeepStream-8.0-76B900?style=flat-square&logo=nvidia)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

**DeepStream 8.0 Python 学习与实践记录**

记录在学习 NVIDIA DeepStream Python 开发过程中遇到的问题、解决方案和实战代码

[English](README_EN.md) | 简体中文

</div>

---

## 📖 项目背景

在学习 [NVIDIA-AI-IOT/deepstream_python_apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps) 官方示例时，我发现：

- ❌ 官方仓库没有开启 Issues，遇到问题难以交流
- ❌ 对环境版本要求极高（DeepStream 8.0 + Ubuntu 24.04）
- ❌ 缺少多流多模型推理的完整示例
- ❌ 示例代码主要针对 Jetson 平台，PC 端部署需要大量修改
- ❌ 容易遇到各种环境配置和运行问题

因此创建此仓库，记录 **Ubuntu 22.04 + DeepStream 8.0 + Docker** 环境下的实践经验，帮助遇到相同问题的开发者。

## ✨ 本项目特点

- ✅ 基于 **Docker 容器**部署，安全可靠，完全可逆
- ✅ 详细记录从环境搭建到运行的**完整流程**
- ✅ 提供**可直接运行**的示例代码和配置
- ✅ 解决官方示例中的**常见 Bug**（如 Vulkan 驱动问题）
- ✅ 包含**多流处理**、**自定义模型**、**RTSP 输出**等实用场景
- ✅ 性能测试数据和优化建议

## 🛠️ 环境配置

### 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS |
| CUDA | 12.0+ / 13.0 |
| NVIDIA 驱动 | 525+ / 580+ |
| GPU | NVIDIA GPU (推荐 RTX 2060+) |
| 显存 | 4GB+ |
| 内存 | 8GB+ |

### 核心依赖

- **Docker** + **NVIDIA Container Toolkit**
- **DeepStream 8.0** (通过 Docker 镜像)
- **Python 3.8+**
- **GStreamer 1.0**

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/RuijieSpace/Deepstream_Python_Stack.git
cd Deepstream_Python_Stack
```

### 2. 安装 Docker 和 NVIDIA Container Toolkit

```bash
# 运行自动安装脚本
bash scripts/install_docker.sh
bash scripts/install_nvidia_toolkit.sh
```

详细步骤请参考：[docs/installation.md](docs/installation.md)

### 3. 拉取 DeepStream 8.0 镜像

```bash
docker pull nvcr.io/nvidia/deepstream:8.0-triton-multiarch
```

### 4. 启动容器

```bash
# 配置 X11 显示（用于视频窗口）
xhost +local:docker

# 启动交互式容器
docker run -it --rm \
  --name deepstream8 \
  --gpus all \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd):/workspace \
  nvcr.io/nvidia/deepstream:8.0-triton-multiarch \
  /bin/bash
```

### 5. 容器内验证环境

```bash
# 检查 DeepStream 版本
deepstream-app --version

# 检查 GPU
nvidia-smi

# 查看 DeepStream 目录
ls /opt/nvidia/deepstream/deepstream/
```

### 6. 运行示例

```bash
# 进入示例目录
cd examples/01_basic_video_detection

# 运行基础检测示例
python3 deepstream_test1_modified.py /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

## 📂 项目结构

```
Deepstream_Python_Stack/
├── README.md                          # 项目说明
├── docs/                              # 详细文档
│   ├── installation.md                # 完整安装指南
│   ├── troubleshooting.md             # 问题排查手册
│   ├── performance_analysis.md        # 性能分析报告
│   └── api_reference.md               # API 参考
├── examples/                          # 示例代码
│   ├── 01_basic_video_detection/      # 官方模型视频测试
│   ├── 02_custom_model/               # 自定义模型推理
│   ├── 03_object_tracking/            # 目标跟踪
│   ├── 04_rtsp_single_stream/         # RTSP 单路输出
│   └── 05_rtsp_multi_stream/          # RTSP 多路输出
├── configs/                           # 配置文件
│   ├── models/                        # 模型配置
│   └── tracker/                       # 跟踪器配置
├── scripts/                           # 自动化脚本
│   ├── install_docker.sh
│   ├── install_nvidia_toolkit.sh
│   └── download_models.sh
└── utils/                             # 工具函数
    ├── pipeline_utils.py
    └── video_utils.py
```

## 📊 示例展示

### 示例 1：官方模型视频检测

**功能**：使用 ResNet-10 模型检测 4 类目标（Vehicle, Person, Bicycle, Roadsign）

**已解决的问题**：
- ❌ `VK_ERROR_INCOMPATIBLE_DRIVER` Vulkan 驱动不兼容
- ✅ 使用 `fakesink` 或修改为 `filesink` 输出

```bash
cd examples/01_basic_video_detection
python3 deepstream_test1_modified.py <video_file>
```

### 示例 2：自定义 YOLOv8 模型推理

**性能数据**（3840×2160 视频，12179 帧）：

| 模型 | 输入尺寸 | 平均 FPS | 总耗时 |
|------|----------|----------|--------|
| YOLOv8n | 640×640 | 497.21 | 25.01s |
| Custom Person Model | 1920×1920 | 310.34 | 39.75s |
| Custom Highway Model | 1920×1920 | 152.76 | 68.06s |

```bash
cd examples/02_custom_model
python3 custom_yolo_inference.py
```

### 示例 3：多目标跟踪

支持 NvDCF、IOU、DeepSORT 等跟踪算法

```bash
cd examples/03_object_tracking
python3 tracking_demo.py
```

### 示例 4：RTSP 多路流输出

**多路性能测试**（3840×2160，YOLOv8n 640×640）：

| 视频流路数 | GPU 利用率 | 状态 |
|-----------|-----------|------|
| 4 路 | ~5% | ✅ 流畅 |
| 8 路 | ~10% | ✅ 流畅 |
| 12 路 | ~15% | ✅ 流畅 |
| 16 路 | ~17% | ✅ 流畅 |

```bash
cd examples/05_rtsp_multi_stream
python3 multi_stream_rtsp.py
```

通过 VLC 或 FFplay 查看输出：
```bash
ffplay rtsp://localhost:8554/stream0
```

## 🐛 常见问题

### 问题 1：VK_ERROR_INCOMPATIBLE_DRIVER

**症状**：运行时出现 Vulkan 驱动错误，窗口无法显示

**解决方案**：
```python
# 方法 1：使用 fakesink（仅输出检测结果）
sink = Gst.ElementFactory.make("fakesink", "fakesink")

# 方法 2：使用 filesink 保存到文件
sink = Gst.ElementFactory.make("filesink", "filesink")
sink.set_property("location", "output.mp4")
```

### 问题 2：GStreamer 插件加载警告

**症状**：大量 `Failed to load plugin` 警告

**说明**：这些警告可以忽略，不影响核心功能

### 问题 3：容器内无法显示窗口

**解决方案**：
```bash
# 在宿主机执行
xhost +local:docker

# 确保容器启动时包含 X11 相关参数
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
```

更多问题请查看：[docs/troubleshooting.md](docs/troubleshooting.md)

## 📚 相关资源

### 官方文档
- [DeepStream SDK 开发指南](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo) - YOLO 模型适配

### 参考仓库
- [deepstream_reference_apps](https://github.com/NVIDIA-AI-IOT/deepstream_reference_apps) - C++ 参考应用

## 💡 为什么选择 Docker？

1. **零风险** - 不会破坏宿主系统环境
2. **完全可逆** - 不需要时删除容器即可
3. **环境一致** - DeepStream 8.0 需要 Ubuntu 24.04，Docker 可在 Ubuntu 22.04 上运行
4. **隔离性好** - DeepStream 的配置与系统底层相关，容器内问题不影响外部

⚠️ **注意**：删除容器时，容器内的所有环境和安装的包都会被删除！建议将重要数据挂载到宿主机。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！

## 📧 联系方式

- **GitHub**: [@RuijieSpace](https://github.com/RuijieSpace)
- **项目地址**: https://github.com/RuijieSpace/Deepstream_Python_Stack

## 📄 开源协议

本项目采用 MIT License 开源协议

---

<div align="center">

**Built with ❤️ by DeepStream Learners**

如果遇到问题，欢迎提 Issue 交流！

</div>
