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
- ✅ **完整的 Python Bindings (pyds) 安装指南**
- ✅ **DeepStream-Yolo 集成支持**

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

### 验证系统环境

```bash
# 检查系统版本
cat /etc/os-release

# 检查 NVIDIA 驱动
nvidia-smi

# 检查 CUDA 版本
nvidia-smi | grep "CUDA Version"
```

**参考配置**：
- 操作系统: Ubuntu 22.04
- CUDA 版本: 13.0
- 驱动版本: 580.65.06

### 核心依赖

- **Docker** + **NVIDIA Container Toolkit**
- **DeepStream 8.0** (通过 Docker 镜像)
- **Python 3.8+**
- **GStreamer 1.0**
- **Python Bindings (pyds)**

## 🚀 完整部署流程

### 第一步：安装 Docker

```bash
# 1. 移除旧版本 Docker（如果有）
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null || true

# 2. 更新软件包索引
sudo apt update

# 3. 安装依赖包
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 4. 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 5. 设置 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. 安装 Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# 7. 验证 Docker 安装
sudo docker run hello-world

# 8. 添加当前用户到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER

# 9. 重新加载用户组（重要！）
newgrp docker

# 10. 再次验证（无需 sudo）
docker run hello-world
```

### 第二步：配置 Docker 镜像加速器

```bash
# 1. 创建或编辑 Docker 配置文件
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

粘贴以下内容：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.sjtug.sjtu.edu.cn"
  ]
}
```

保存并退出（`Ctrl+X`, `Y`, `Enter`）

```bash
# 2. 重启 Docker 服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 3. 验证配置
sudo docker info | grep -A 5 "Registry Mirrors"

# 4. 测试
docker run hello-world
```

### 第三步：安装 NVIDIA Container Toolkit

```bash
# 1. 添加 NVIDIA Container Toolkit 仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. 更新包列表
sudo apt update

# 3. 安装 NVIDIA Container Toolkit
sudo apt install -y nvidia-container-toolkit

# 4. 配置 Docker 以使用 NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# 5. 重启 Docker 服务
sudo systemctl restart docker

# 6. 验证 GPU 在 Docker 中可用
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### 第四步：拉取 DeepStream 8.0 镜像

```bash
# 拉取 DeepStream 8.0 镜像（约 8GB，需要几分钟）
docker pull nvcr.io/nvidia/deepstream:8.0-triton-multiarch

# 如果上面的镜像不可用，可以尝试：
# docker pull nvcr.io/nvidia/deepstream:8.0-gc-triton-devel

# 查看镜像
docker images | grep deepstream
```

### 第五步：创建工作目录

```bash
# 在宿主机创建项目目录结构
mkdir -p ~/deepstream8_project
cd ~/deepstream8_project

# 创建子目录
mkdir -p configs videos output scripts models

# 查看目录结构
tree -L 1  # 或使用 ls -la
```

### 第六步：配置 X11 显示（可选）

⚠️ **注意**：DeepStream 最适配的平台是 Nvidia Jetson，在 PC 端可能无法正常显示窗口。建议使用 RTSP 协议将视频流传输到容器外部进行查看。

```bash
# 允许 Docker 容器访问 X11 显示
xhost +local:docker

# 如果提示 xhost 命令不存在，安装它：
# sudo apt install x11-xserver-utils
```

### 第七步：启动容器

```bash
docker run -it --rm \
  --name deepstream_python_stack \
  --gpus all \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v ~/deepstream8_project:/opt/nvidia/deepstream/deepstream/my_apps \
  nvcr.io/nvidia/deepstream:8.0-triton-multiarch \
  /bin/bash
```

**参数说明**：
- `--name`: 容器名称
- `--gpus all`: 使用所有 GPU
- `--network host`: 使用宿主机网络（用于 RTSP 流）
- `-e DISPLAY`: 传递显示环境变量
- `-v`: 挂载目录（宿主机路径:容器路径）

### 第八步：容器内环境配置

#### 8.1 克隆项目仓库

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/RuijieSpace/Deepstream_Python_Stack.git
cd Deepstream_Python_Stack
```

#### 8.2 安装系统依赖

```bash
apt-get update
apt-get install -y \
    git \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gst-1.0 \
    cmake \
    g++ \
    make \
    pkg-config \
    libglib2.0-dev \
    libgstreamer1.0-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pybind11-dev \
    python3-pybind11
```

#### 8.3 安装 Python 依赖

```bash
pip3 install pybind11 numpy cuda-python
```

#### 8.4 编译安装 Python Bindings (pyds)

```bash
# 进入 DeepStream Python bindings 源码目录
cd /opt/nvidia/deepstream/deepstream/sources

# 初始化子模块
git submodule update --init --recursive

# 创建构建目录
cd bindings
rm -rf build && mkdir build && cd build

# 配置 CMake（自动检测 Python 版本）
cmake .. \
    -DPYTHON_MAJOR_VERSION=3 \
    -DPYTHON_MINOR_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)

# 编译（使用所有 CPU 核心加速）
make -j$(nproc)

# 验证生成的文件
ls -lh pyds.so
```

#### 8.5 安装 pyds 到 Python 环境

```bash
# 获取 Python site-packages 路径
PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Python site-packages 路径: $PYTHON_SITE"

# 复制 pyds.so 到 Python 路径
cp pyds.so "$PYTHON_SITE/"

# 验证安装
python3 -c "import pyds; print('✓ pyds 导入成功，版本:', pyds.__version__)"
```

**成功标志**：应该看到 `✓ pyds 导入成功` 的提示

#### 8.6 安装 DeepStream-Yolo（可选）

如果需要使用 YOLO 模型，需要安装 DeepStream-Yolo：

```bash
# 克隆 DeepStream-Yolo 仓库
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/marcoslucianops/DeepStream-Yolo.git
cd DeepStream-Yolo

# 设置 CUDA 版本（根据 DeepStream 版本选择）
export CUDA_VER=12.8  # DeepStream 8.0 对应 CUDA 12.8

# 编译自定义 YOLO 插件
make -C nvdsinfer_custom_impl_Yolo clean && \
make -C nvdsinfer_custom_impl_Yolo
```

**CUDA 版本对照表**：
- DeepStream 8.0 = CUDA 12.8
- DeepStream 7.1 = CUDA 12.6
- DeepStream 7.0 / 6.4 = CUDA 12.2
- DeepStream 6.3 = CUDA 12.1
- DeepStream 6.2 = CUDA 11.8

### 第九步：运行示例测试

#### 测试 1：官方模型检测

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/examples/01_deepstream_test_1

python3 deepstream_test_1.py \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

**成功输出示例**：

```
0:00:00.264204810 227925 0x244e1920 INFO nvinfer gstnvinfer_impl.cpp:343:notifyLoadModelStatus:
<primary-inference> [UID 1]: Load new model:dstest1_pgie_config.txt sucessfully

Frame Number=0 Number of Objects=17 Vehicle_count=11 Person_count=6
Frame Number=100 Number of Objects=23 Vehicle_count=15 Person_count=8
Frame Number=200 Number of Objects=27 Vehicle_count=20 Person_count=7
...
nvstreammux: Successfully handled EOS for source_id=0
End-of-stream
Video saved to: /opt/nvidia/deepstream/deepstream/my_apps/test_data/output_video.mp4
```

#### 测试 2：查看保存的视频

如果挂载了宿主机目录，可以在宿主机查看输出视频：

```bash
# 在宿主机执行
cd ~/deepstream8_project/test_data
ls -lh output_video.mp4
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
│   ├── 01_deepstream_test_1/          # 官方模型视频测试
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
cd examples/01_deepstream_test_1
python3 deepstream_test_1.py <video_file>
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

# 方法 3：使用 RTSP 输出（推荐）
# 见示例 04 和 05
```

### 问题 2：pyds 导入失败

**症状**：`ImportError: No module named 'pyds'`

**解决方案**：
```bash
# 确认 pyds.so 是否存在
python3 -c "import site; print(site.getsitepackages()[0])"
ls -l /usr/local/lib/python3.*/dist-packages/pyds.so

# 重新安装 pyds
cd /opt/nvidia/deepstream/deepstream/sources/bindings/build
PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
cp pyds.so "$PYTHON_SITE/"
```

### 问题 3：GStreamer 插件加载警告

**症状**：大量 `Failed to load plugin` 警告

**说明**：这些警告可以忽略，不影响核心功能。DeepStream 会尝试加载多个可选插件，未找到时会产生警告。

### 问题 4：容器内无法显示窗口

**解决方案**：
```bash
# 在宿主机执行
xhost +local:docker

# 确保容器启动时包含 X11 相关参数
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
```

**推荐方案**：使用 RTSP 协议将视频流传输到容器外部查看，避免 X11 显示问题。

### 问题 5：删除容器后环境丢失

**说明**：这是 Docker 的正常行为。删除容器时，容器内的所有环境和安装的包都会被删除。

**解决方案**：
```bash
# 方法 1：不使用 --rm 参数，保留容器
docker run -it --name deepstream_python_stack ...

# 停止后重新进入
docker start deepstream_python_stack
docker exec -it deepstream_python_stack /bin/bash

# 方法 2：将重要数据挂载到宿主机
-v ~/deepstream8_project:/workspace

# 方法 3：创建自定义镜像保存环境
docker commit deepstream_python_stack my_deepstream:v1
```

更多问题请查看：[docs/troubleshooting.md](docs/troubleshooting.md)

## 📚 相关资源

### 官方文档
- [DeepStream SDK 开发指南](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo) - YOLO 模型适配

### 参考仓库
- [deepstream_reference_apps](https://github.com/NVIDIA-AI-IOT/deepstream_reference_apps) - C++ 参考应用（生产级完整方案）

### 核心功能对比

| 仓库 | 语言 | 适用平台 | 特点 |
|------|------|----------|------|
| deepstream_python_apps | Python | Jetson/x86 | 官方示例，需要修改 |
| DeepStream-Yolo | C++/Python | x86 | YOLO 模型适配，GPU 后处理优化 |
| deepstream_reference_apps | C++ | Jetson/x86 | 生产级方案，多模型并行 |
| **本项目** | Python | x86 (Ubuntu 22.04) | Docker 部署，开箱即用 |

## 💡 为什么选择 Docker？

### ✅ Docker 方案的优势

1. **零风险** - 不会破坏宿主系统环境
2. **完全可逆** - 不需要时删除容器即可
3. **环境一致** - DeepStream 8.0 需要 Ubuntu 24.04，Docker 可在 Ubuntu 22.04 上运行
4. **隔离性好** - DeepStream 的配置与系统底层相关，容器内问题不影响外部
5. **易于分发** - 可以打包为镜像，在其他机器快速部署

### ⚠️ 注意事项

- 删除容器时，容器内的所有环境和安装的包都会被删除
- 建议将重要数据和代码挂载到宿主机
- 使用 `docker commit` 可以保存配置好的环境为新镜像

## 🎯 快速命令参考

### Docker 容器管理

```bash
# 启动新容器
docker run -it --rm --name deepstream8 --gpus all ...

# 停止容器
docker stop deepstream8

# 启动已停止的容器
docker start deepstream8

# 进入运行中的容器
docker exec -it deepstream8 /bin/bash

# 查看容器列表
docker ps -a

# 删除容器
docker rm deepstream8

# 保存容器为镜像
docker commit deepstream8 my_deepstream:v1
```

### 常用验证命令

```bash
# 验证 GPU
nvidia-smi

# 验证 DeepStream
deepstream-app --version

# 验证 Python Bindings
python3 -c "import pyds; print(pyds.__version__)"

# 查看 GStreamer 插件
gst-inspect-1.0 nvinfer
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📧 联系方式

- **GitHub**: [@RuijieSpace](https://github.com/RuijieSpace)
- **项目地址**: https://github.com/RuijieSpace/Deepstream_Python_Stack

## 📄 开源协议

本项目采用 MIT License 开源协议

---

<div align="center">

**Built with ❤️ by DeepStream Learners**

如果遇到问题，欢迎提 Issue 交流！

[![GitHub stars](https://img.shields.io/github/stars/RuijieSpace/Deepstream_Python_Stack?style=social)](https://github.com/RuijieSpace/Deepstream_Python_Stack)
[![GitHub forks](https://img.shields.io/github/forks/RuijieSpace/Deepstream_Python_Stack?style=social)](https://github.com/RuijieSpace/Deepstream_Python_Stack)

</div>

