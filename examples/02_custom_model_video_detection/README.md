# Custom Model Video Detection Guide

## 02_custom_model - 自定义模型视频检测

[English](#english-version) | [中文](#中文版本)

---

## 中文版本

### 📖 概述

本示例展示如何在 DeepStream 中使用自定义 YOLOv8 模型进行视频目标检测。包含完整的模型转换、配置和推理流程。

### ✨ 功能特点

- ✅ 支持 YOLOv8 系列模型（n/s/m/l/x）
- ✅ 自定义输入尺寸（默认 640×640，可调整）
- ✅ 动态 batch size 支持
- ✅ ONNX 模型转换和优化
- ✅ TensorRT 加速推理
- ✅ 性能监控和 FPS 统计

### 📋 前置条件

确保你已经完成了基础环境配置：

```bash
# 1. DeepStream 8.0 环境已安装
deepstream-app --version

# 2. Python Bindings (pyds) 已安装
python3 -c "import pyds; print(pyds.__version__)"

# 3. DeepStream-Yolo 已编译
ls /opt/nvidia/deepstream/deepstream/my_apps/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
```

如果未完成，请参考主 README 的[完整部署流程](../../README.md#完整部署流程)。

---

## 🚀 快速开始

### 步骤 1：安装 DeepStream-Yolo

如果还没有安装 DeepStream-Yolo，执行以下命令：

```bash
# 进入工作目录
cd /opt/nvidia/deepstream/deepstream/my_apps

# 克隆 DeepStream-Yolo 仓库
git clone https://github.com/marcoslucianops/DeepStream-Yolo.git
cd DeepStream-Yolo

# 设置 CUDA 版本（根据 DeepStream 版本选择）
export CUDA_VER=12.8  # DeepStream 8.0

# 编译自定义库
make -C nvdsinfer_custom_impl_Yolo clean && \
make -C nvdsinfer_custom_impl_Yolo

# 验证编译
ls -lh nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
```

**CUDA 版本对照表**：

| DeepStream 版本 | CUDA 版本 |
|----------------|-----------|
| 8.0 | 12.8 |
| 7.1 | 12.6 |
| 7.0 / 6.4 | 12.2 |
| 6.3 | 12.1 |
| 6.2 | 11.8 |
| 6.1.1 | 11.7 |
| 6.1 | 11.6 |
| 6.0.1 / 6.0 | 11.4 |
| 5.1 | 11.1 |

---

### 步骤 2：准备 YOLOv8 环境

```bash
# 克隆 ultralytics 仓库
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/ultralytics/ultralytics.git
cd ultralytics

# 安装依赖
pip3 install -e .
pip3 install onnx onnxslim onnxruntime tensorrt
```

---

### 步骤 3：复制模型转换脚本

```bash
# 复制修改好的转换脚本
cp /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/utils/export_yoloV8.py \
   /opt/nvidia/deepstream/deepstream/my_apps/ultralytics/
```

**脚本改进说明**：
我们的转换脚本已解决以下问题：
1. ✅ PyTorch 2.6+ `weights_only` 参数问题
2. ✅ TorchDynamo 导出兼容性问题
3. ✅ ONNX 优化和简化

---

### 步骤 4：转换模型为 ONNX

#### 4.1 基础转换（默认 640×640）

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/ultralytics

python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    --dynamic
```

#### 4.2 自定义输入尺寸

```bash
# 方式 1：正方形输入（1280×1280）
python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    -s 1280 \
    --dynamic

# 方式 2：矩形输入（1920×1080）
python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    -s 1920 1080 \
    --dynamic
```

#### 4.3 其他常用参数

```bash
# 简化 ONNX 模型（DeepStream >= 6.0）
python3 export_yoloV8.py -w model.pt --dynamic --simplify

# 静态 batch size（例如 batch=4）
python3 export_yoloV8.py -w model.pt --batch 4

# 指定 opset 版本（DeepStream 5.1 使用 opset 12）
python3 export_yoloV8.py -w model.pt --dynamic --opset 12
```

**参数说明**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `-w, --weights` | 模型权重路径 | `-w yolov8n.pt` |
| `-s, --size` | 输入尺寸 | `-s 640` 或 `-s 1920 1080` |
| `--dynamic` | 动态 batch size | `--dynamic` |
| `--batch` | 静态 batch size | `--batch 4` |
| `--simplify` | 简化 ONNX 模型 | `--simplify` |
| `--opset` | ONNX opset 版本 | `--opset 12` |

---

### 步骤 5：组织模型文件

将导出的 ONNX 模型和标签文件移动到 models 目录：

```bash
# 导出的 ONNX 模型默认名称为 yolov8.onnx
# 移动到 models 目录（根据你的模型类型命名）
mv yolov8.onnx \
   /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/your_model_name.onnx

# 如果有标签文件，也一起移动
mv labels.txt \
   /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/your_labels.txt

# 查看 models 目录内容
ls -lh /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/
```

**models 目录结构示例**：
```
models/
├── yolov8n_person.onnx       # 人员检测模型
├── yolov8n_vehicle.onnx      # 车辆检测模型
├── yolov8s_highway.onnx      # 高速公路场景模型
├── labels_coco.txt           # COCO 数据集标签
├── labels_custom.txt         # 自定义标签
└── ...                       # 其他模型文件
```

---

### 步骤 6：修改配置文件

编辑配置文件：
```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/examples/02_custom_model_video_detection
nano dstest1_pgie_config.txt
```

**关键配置项（需要修改的部分）**：

```ini
[property]
gpu-id=0
net-scale-factor=0.0039215697906911373

# 1. 修改为你的 ONNX 模型路径（相对路径或绝对路径）
model-file=../../models/your_model_name.onnx

# 2. 修改为你的标签文件路径
labelfile-path=../../models/your_labels.txt

# 3. 修改为你的模型类别数量
num-detected-classes=80  # 例如 COCO 数据集是 80 类

# 4. 修改输入尺寸（需与导出时的尺寸一致）
infer-dims=3;640;640  # 格式：channels;height;width
# 如果导出时使用 -s 1280，这里改为 3;1280;1280

# TensorRT 引擎文件（首次运行会自动生成）
model-engine-file=../../models/your_model_b1_gpu0_fp16.engine

# 推理精度（2=FP16，速度更快，推荐）
network-mode=2

batch-size=1
interval=0
gie-unique-id=1

# 自定义库路径（DeepStream-Yolo 的解析库）
custom-lib-path=/opt/nvidia/deepstream/deepstream/my_apps/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
parse-bbox-func-name=NvDsInferParseYolo

# 后处理参数
cluster-mode=2
nms-iou-threshold=0.45
pre-cluster-threshold=0.25

maintain-aspect-ratio=1
symmetric-padding=1
```

**配置参数说明**：

| 参数 | 说明 | 示例值 | 注意事项 |
|------|------|--------|---------|
| `model-file` | ONNX 模型路径 | `../../models/yolov8n.onnx` | 必须与实际文件路径一致 |
| `labelfile-path` | 标签文件路径 | `../../models/labels.txt` | 每行一个类别名称 |
| `num-detected-classes` | 类别数量 | `80` | 必须与模型训练时的类别数一致 |
| `infer-dims` | 输入尺寸 | `3;640;640` | 必须与 ONNX 导出时一致 |
| `network-mode` | 推理精度 | `0`=FP32, `2`=FP16 | FP16 推荐（速度快，精度损失小） |
| `pre-cluster-threshold` | 置信度阈值 | `0.25` | 降低可检测更多目标，但误检增加 |
| `nms-iou-threshold` | NMS IOU 阈值 | `0.45` | 控制重叠框的过滤程度 |

---

### 步骤 7：运行检测

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/examples/02_custom_model_video_detection

# 运行示例
python3 01_custom_model_video_detection.py \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

**预期输出**：

```
=======================================================
Using config file: dstest1_pgie_config.txt
=======================================================

0:00:00.523410234 12345 0x7f8b4c000b20 INFO nvinfer gstnvinfer_impl.cpp:343:
Loading ONNX model: ../../models/yolov8n.onnx
Building TensorRT engine...
[TensorRT] This may take a few minutes...

Frame Number=0 Number of Objects=12 person=3 car=7 truck=2
Frame Number=100 Number of Objects=15 person=4 car=9 truck=2
Frame Number=200 Number of Objects=18 person=5 car=11 truck=2
...

Average FPS: 487.3
Total processing time: 3.12s
Video saved to: output/custom_detection_output.mp4
```

---

## 🐛 常见问题排查

### 问题 1：模型加载失败 - `weights_only` 错误

**完整错误信息**：
```python
_pickle.UnpicklingError: Weights only load failed. This file can still be loaded, 
to do so you have two options, do those steps only if you trust the source of the checkpoint.
(1) In PyTorch 2.6, we changed the default value of the `weights_only` argument 
in `torch.load` from `False` to `True`.
```

**原因**：PyTorch 2.6+ 默认启用了安全加载模式

**解决方案**：

修改 `export_yoloV8.py` 第 38 行：

```python
# 修改前
ckpt = torch.load(weights, map_location='cpu')

# 修改后
ckpt = torch.load(weights, map_location='cpu', weights_only=False)
```

---

### 问题 2：TorchDynamo 导出错误

**完整错误信息**：
```python
AttributeError: 'float' object has no attribute 'node'
While executing %item : [num_users=1] = call_function[target=torch.ops.aten.item.default]
```

**原因**：TorchDynamo 与 YOLOv8 的某些操作不兼容

**解决方案**：

修改 `export_yoloV8.py` 的 `torch.onnx.export()` 调用：

```python
torch.onnx.export(
    model, onnx_input_im, onnx_output_file,
    verbose=False, 
    opset_version=args.opset,
    do_constant_folding=True,
    input_names=['input'], 
    output_names=['output'],
    dynamic_axes=dynamic_axes if args.dynamic else None,
    dynamo=False  # 添加这一行
)
```

---

### 问题 3：TensorRT 引擎构建失败

**症状**：首次运行时卡在 "Building TensorRT engine..."

**原因**：TensorRT 正在优化模型，这是正常现象

**解决方案**：

1. **耐心等待**：首次构建可能需要 2-10 分钟，取决于模型大小和 GPU
2. **查看进度**：
   ```bash
   # 查看 GPU 使用情况
   watch -n 1 nvidia-smi
   ```
3. **重用引擎**：引擎文件会保存在配置中指定的路径，后续运行会直接加载

**加速技巧**：
```ini
# 在配置文件中指定固定的引擎文件路径
model-engine-file=../../models/yolov8n_custom/model_b1_gpu0_fp16.engine

# 使用 FP16 精度（更快，精度损失很小）
network-mode=2
```

---

### 问题 4：检测结果为空或异常

**可能原因和解决方案**：

#### 原因 1：置信度阈值过高
```ini
# 降低阈值
pre-cluster-threshold=0.1  # 从 0.25 降低到 0.1
```

#### 原因 2：输入尺寸不匹配
```ini
# 在 dstest1_pgie_config.txt 中确保与导出时一致
infer-dims=3;640;640  # 需要与 export_yoloV8.py 中的 -s 参数一致
```

#### 原因 3：标签文件错误
```bash
# 检查标签文件格式（每行一个类别，不要有空行）
cat /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/your_labels.txt

# 标签文件示例（正确格式）
person
bicycle
car
motorcycle
# ... 每行一个类别，无额外空行
```

#### 原因 4：NMS 参数不当
```ini
# 在 dstest1_pgie_config.txt 中调整 NMS 参数
nms-iou-threshold=0.45
cluster-mode=2  # 2=DBSCAN, 3=NMS
```

---

### 问题 5：内存不足 (OOM)

**症状**：`CUDA out of memory` 错误

**解决方案**：

```ini
# 方法 1：降低 batch size
batch-size=1

# 方法 2：使用更小的输入尺寸
infer-dims=3;416;416  # 从 640 降低到 416

# 方法 3：使用 INT8 精度
network-mode=1
```

---

## 📊 性能优化建议

### 1. 精度 vs 速度权衡

| 精度模式 | 速度 | 精度损失 | 推荐场景 |
|---------|------|---------|---------|
| FP32 | 基准 | 0% | 开发调试 |
| FP16 | 1.5-2× | <1% | 生产环境（推荐） |
| INT8 | 2-3× | 1-3% | 实时处理 |

**配置示例**：
```ini
# 在 dstest1_pgie_config.txt 中设置
# FP16 模式（推荐）
network-mode=2
```

### 2. 输入尺寸优化

| 输入尺寸 | 速度 | 精度 | 推荐场景 |
|---------|------|------|---------|
| 320×320 | 最快 | 低 | 实时低分辨率 |
| 416×416 | 快 | 中 | 一般场景 |
| 640×640 | 中 | 高 | 标准场景（推荐） |
| 1280×1280 | 慢 | 最高 | 高精度需求 |

### 3. Batch Size 调整

```bash
# 测试不同 batch size 的性能
# 编辑 dstest1_pgie_config.txt，修改 batch-size 参数
for bs in 1 2 4 8; do
    echo "Testing batch_size=$bs"
    sed -i "s/batch-size=.*/batch-size=$bs/" dstest1_pgie_config.txt
    python3 01_custom_model_video_detection.py test_video.mp4
done
```

**建议**：
- 单流推理：`batch-size=1`
- 多流推理：`batch-size=4` 或 `batch-size=8`

### 4. 多流处理

```python
# 示例：处理 4 路视频流
streams = [
    "rtsp://camera1/stream",
    "rtsp://camera2/stream",
    "rtsp://camera3/stream",
    "rtsp://camera4/stream"
]

# 配置 streammux
streammux.set_property("batch-size", len(streams))
```

---

## 📈 性能基准测试

### 测试环境
- GPU: NVIDIA RTX 3080
- 视频: 3840×2160, 12179 帧
- DeepStream: 8.0
- TensorRT: 8.6

### 测试结果

| 模型 | 输入尺寸 | Batch Size | 精度 | 平均 FPS | 总耗时 |
|------|---------|-----------|------|---------|--------|
| YOLOv8n | 640×640 | 1 | FP32 | 497.21 | 24.49s |
| YOLOv8n | 640×640 | 1 | FP16 | 623.45 | 19.54s |
| YOLOv8s | 640×640 | 1 | FP16 | 412.33 | 29.54s |
| YOLOv8m | 640×640 | 1 | FP16 | 287.56 | 42.35s |
| YOLOv8n | 1280×1280 | 1 | FP16 | 185.32 | 65.73s |
| Custom Model | 1920×1920 | 1 | FP16 | 310.34 | 39.25s |

---

## 📁 完整文件结构

```
Deepstream_Python_Stack/
├── examples/
│   └── 02_custom_model_video_detection/
│       ├── README.md                              # 本文档
│       ├── dstest1_pgie_config.txt               # 模型配置文件 ⭐
│       ├── 01_custom_model_video_detection.py    # 单视频检测脚本
│       ├── 02_custom_model_rtsp_output.py        # RTSP 输出脚本
│       └── output/                               # 输出目录
│           └── custom_detection_output.mp4
└── models/                                        # 模型存储目录 ⭐
    ├── yolov8n.onnx                              # YOLOv8n 模型
    ├── yolov8n_person.onnx                       # 人员检测模型
    ├── yolov8s_vehicle.onnx                      # 车辆检测模型
    ├── labels_coco.txt                           # COCO 标签文件
    ├── labels_custom.txt                         # 自定义标签文件
    └── model_b1_gpu0_fp16.engine                 # TensorRT 引擎文件（自动生成）
```

**目录说明**：
- `examples/02_custom_model_video_detection/` - 示例代码和配置文件
- `models/` - 所有模型相关文件的统一存储位置
- `dstest1_pgie_config.txt` - 核心配置文件，需要根据实际模型路径修改

---

## 🔗 相关资源

### 官方文档
- [DeepStream-Yolo GitHub](https://github.com/marcoslucianops/DeepStream-Yolo)
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [TensorRT Documentation](https://docs.nvidia.com/deeplearning/tensorrt/)

### 模型下载
- [YOLOv8 预训练模型](https://github.com/ultralytics/assets/releases)
- [COCO 数据集](https://cocodataset.org/)

### 进阶教程
- [自定义数据集训练](https://docs.ultralytics.com/modes/train/)
- [模型导出详解](https://docs.ultralytics.com/modes/export/)
- [TensorRT 优化指南](https://docs.nvidia.com/deeplearning/tensorrt/developer-guide/)

---

## 🤝 贡献

如果你遇到问题或有改进建议，欢迎：
1. 提交 Issue
2. 提交 Pull Request
3. 在讨论区分享经验

---

## 📄 许可证

本项目采用 MIT License 开源协议

---

<div align="center">

**下一步**：尝试 [多目标跟踪](../03_object_tracking/README.md) 或 [RTSP 流输出](../04_rtsp_single_stream/README.md)

</div>

---

## English Version

### 📖 Overview

This example demonstrates how to use custom YOLOv8 models for video object detection in DeepStream, including complete model conversion, configuration, and inference workflow.

### ✨ Features

- ✅ Support for YOLOv8 series models (n/s/m/l/x)
- ✅ Custom input sizes (default 640×640, adjustable)
- ✅ Dynamic batch size support
- ✅ ONNX model conversion and optimization
- ✅ TensorRT accelerated inference
- ✅ Performance monitoring and FPS statistics

### 📋 Prerequisites

Ensure you have completed the basic environment setup:

```bash
# 1. DeepStream 8.0 environment installed
deepstream-app --version

# 2. Python Bindings (pyds) installed
python3 -c "import pyds; print(pyds.__version__)"

# 3. DeepStream-Yolo compiled
ls /opt/nvidia/deepstream/deepstream/my_apps/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
```

If not completed, refer to the main README's [Complete Deployment Process](../../README_EN.md#complete-deployment-process).

---

## 🚀 Quick Start

### Step 1: Install DeepStream-Yolo

If you haven't installed DeepStream-Yolo yet:

```bash
# Navigate to working directory
cd /opt/nvidia/deepstream/deepstream/my_apps

# Clone DeepStream-Yolo repository
git clone https://github.com/marcoslucianops/DeepStream-Yolo.git
cd DeepStream-Yolo

# Set CUDA version (according to DeepStream version)
export CUDA_VER=12.8  # DeepStream 8.0

# Compile custom library
make -C nvdsinfer_custom_impl_Yolo clean && \
make -C nvdsinfer_custom_impl_Yolo

# Verify compilation
ls -lh nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
```

**CUDA Version Reference**:

| DeepStream Version | CUDA Version |
|-------------------|--------------|
| 8.0 | 12.8 |
| 7.1 | 12.6 |
| 7.0 / 6.4 | 12.2 |
| 6.3 | 12.1 |
| 6.2 | 11.8 |

---

### Step 2: Setup YOLOv8 Environment

```bash
# Clone ultralytics repository
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/ultralytics/ultralytics.git
cd ultralytics

# Install dependencies
pip3 install -e .
pip3 install onnx onnxslim onnxruntime tensorrt
```

---

### Step 3: Copy Model Conversion Script

```bash
# Copy the modified conversion script
cp /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/utils/export_yoloV8.py \
   /opt/nvidia/deepstream/deepstream/my_apps/ultralytics/
```

**Script Improvements**:
Our conversion script has resolved:
1. ✅ PyTorch 2.6+ `weights_only` parameter issue
2. ✅ TorchDynamo export compatibility issue
3. ✅ ONNX optimization and simplification

---

### Step 4: Convert Model to ONNX

#### 4.1 Basic Conversion (default 640×640)

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/ultralytics

python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    --dynamic
```

#### 4.2 Custom Input Size

```bash
# Method 1: Square input (1280×1280)
python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    -s 1280 \
    --dynamic

# Method 2: Rectangle input (1920×1080)
python3 export_yoloV8.py \
    -w /path/to/your/yolov8n.pt \
    -s 1920 1080 \
    --dynamic
```

---

### Step 5: Organize Model Files

```bash
# Create model directory
MODEL_NAME="yolov8n_custom"
mkdir -p /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/$MODEL_NAME

# Move ONNX model
mv yolov8.onnx \
   /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/$MODEL_NAME/

# Create labels file
cat > /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/models/$MODEL_NAME/labels.txt << EOF
person
car
truck
bus
EOF
```

---

### Step 6: Configure Model Parameters

Edit configuration file `configs/models/custom_yolov8_config.txt`:

```ini
[property]
gpu-id=0
net-scale-factor=0.0039215697906911373
model-file=../../models/yolov8n_custom/yolov8.onnx
labelfile-path=../../models/yolov8n_custom/labels.txt
num-detected-classes=4
infer-dims=3;640;640

# TensorRT engine configuration
model-engine-file=../../models/yolov8n_custom/model_b1_gpu0_fp16.engine
batch-size=1
network-mode=2  # 0=FP32, 2=FP16
interval=0
gie-unique-id=1

# Custom library path
custom-lib-path=/opt/nvidia/deepstream/deepstream/my_apps/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so
parse-bbox-func-name=NvDsInferParseYolo

# Post-processing parameters
cluster-mode=2
nms-iou-threshold=0.45
pre-cluster-threshold=0.25
```

---

### Step 7: Run Detection

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/examples/02_custom_model

python3 01_custom_model_video_detection.py \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

---

## 🐛 Troubleshooting

### Issue 1: Model Loading Failed - `weights_only` Error

**Solution**: Modify line 38 in `export_yoloV8.py`:

```python
ckpt = torch.load(weights, map_location='cpu', weights_only=False)
```

---

### Issue 2: TorchDynamo Export Error

**Solution**: Add `dynamo=False` to `torch.onnx.export()`:

```python
torch.onnx.export(
    model, onnx_input_im, onnx_output_file,
    ...,
    dynamo=False
)
```

---

## 📊 Performance Benchmarks

### Test Environment
- GPU: NVIDIA RTX 3080
- Video: 3840×2160, 12179 frames
- DeepStream: 8.0

### Results

| Model | Input Size | Precision | Avg FPS | Total Time |
|-------|-----------|-----------|---------|------------|
| YOLOv8n | 640×640 | FP16 | 623.45 | 19.54s |
| YOLOv8s | 640×640 | FP16 | 412.33 | 29.54s |
| YOLOv8m | 640×640 | FP16 | 287.56 | 42.35s |

---

<div align="center">

**Next Steps**: Try [Object Tracking](../03_object_tracking/README.md) or [RTSP Streaming](../04_rtsp_single_stream/README.md)

</div>