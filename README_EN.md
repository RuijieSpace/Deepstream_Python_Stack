# Deepstream_Python_Stack

<div align="center">

![DeepStream](https://img.shields.io/badge/DeepStream-8.0-76B900?style=flat-square&logo=nvidia)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

**DeepStream 8.0 Python Learning & Practice Notes**

Recording issues, solutions, and practical code encountered while learning NVIDIA DeepStream Python development

---

**Languages**

[🇺🇸 English](README_EN.md) | [🇨🇳 简体中文](README.md)

</div>

---

## 📖 Background

While learning from the official [NVIDIA-AI-IOT/deepstream_python_apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps) examples, I discovered:

- ❌ Official repository has Issues disabled, making it hard to communicate problems
- ❌ Extremely strict environment requirements (DeepStream 8.0 + Ubuntu 24.04)
- ❌ Lack of complete multi-stream multi-model inference examples
- ❌ Sample code mainly targets Jetson platform, requiring extensive modifications for PC deployment
- ❌ Easy to encounter various environment configuration and runtime issues

Therefore, this repository was created to document practical experiences with **Ubuntu 22.04 + DeepStream 8.0 + Docker** environment, helping developers facing similar challenges.

## ✨ Project Highlights

- ✅ **Docker-based** deployment: safe, reliable, and completely reversible
- ✅ **Complete workflow** documented from environment setup to execution
- ✅ **Ready-to-run** example code and configurations
- ✅ Solves **common bugs** in official examples (e.g., Vulkan driver issues)
- ✅ Includes practical scenarios: **multi-stream processing**, **custom models**, **RTSP output**
- ✅ Performance test data and optimization recommendations

## 🛠️ Environment Setup

### System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Ubuntu 22.04 LTS |
| CUDA | 12.0+ / 13.0 |
| NVIDIA Driver | 525+ / 580+ |
| GPU | NVIDIA GPU (RTX 2060+ recommended) |
| VRAM | 4GB+ |
| RAM | 8GB+ |

### Core Dependencies

- **Docker** + **NVIDIA Container Toolkit**
- **DeepStream 8.0** (via Docker image)
- **Python 3.8+**
- **GStreamer 1.0**

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/RuijieSpace/Deepstream_Python_Stack.git
cd Deepstream_Python_Stack
```

### 2. Install Docker and NVIDIA Container Toolkit

```bash
# Run automated installation scripts
bash scripts/install_docker.sh
bash scripts/install_nvidia_toolkit.sh
```

For detailed steps, see: [docs/en/installation.md](docs/en/installation.md)

### 3. Pull DeepStream 8.0 Image

```bash
docker pull nvcr.io/nvidia/deepstream:8.0-triton-multiarch
```

### 4. Start Container

```bash
# Configure X11 display (for video windows)
xhost +local:docker

# Start interactive container
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

### 5. Verify Environment Inside Container

```bash
# Check DeepStream version
deepstream-app --version

# Check GPU
nvidia-smi

# View DeepStream directory
ls /opt/nvidia/deepstream/deepstream/
```

### 6. Run Examples

```bash
# Navigate to example directory
cd examples/01_basic_video_detection

# Run basic detection example
python3 deepstream_test1_modified.py /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

## 📂 Project Structure

```
Deepstream_Python_Stack/
├── README.md                          # Chinese documentation
├── README_EN.md                       # English documentation
├── docs/                              # Detailed documentation
│   ├── zh/                            # Chinese docs
│   │   ├── installation.md
│   │   ├── troubleshooting.md
│   │   └── performance_analysis.md
│   └── en/                            # English docs
│       ├── installation.md
│       ├── troubleshooting.md
│       └── performance_analysis.md
├── examples/                          # Example code
│   ├── 01_basic_video_detection/      # Official model video test
│   ├── 02_custom_model/               # Custom model inference
│   ├── 03_object_tracking/            # Object tracking
│   ├── 04_rtsp_single_stream/         # RTSP single stream output
│   └── 05_rtsp_multi_stream/          # RTSP multi-stream output
├── configs/                           # Configuration files
│   ├── models/                        # Model configs
│   └── tracker/                       # Tracker configs
├── scripts/                           # Automation scripts
│   ├── install_docker.sh
│   ├── install_nvidia_toolkit.sh
│   └── download_models.sh
└── utils/                             # Utility functions
    ├── pipeline_utils.py
    └── video_utils.py
```

## 📊 Example Demonstrations

### Example 1: Official Model Video Detection

**Features**: Use ResNet-10 model to detect 4 object classes (Vehicle, Person, Bicycle, Roadsign)

**Solved Issues**:
- ❌ `VK_ERROR_INCOMPATIBLE_DRIVER` Vulkan driver incompatibility
- ✅ Use `fakesink` or modified `filesink` output

```bash
cd examples/01_basic_video_detection
python3 deepstream_test1_modified.py <video_file>
```

### Example 2: Custom YOLOv8 Model Inference

**Performance Data** (3840×2160 video, 12179 frames):

| Model | Input Size | Avg FPS | Total Time |
|-------|------------|---------|------------|
| YOLOv8n | 640×640 | 497.21 | 25.01s |
| Custom Person Model | 1920×1920 | 310.34 | 39.75s |
| Custom Highway Model | 1920×1920 | 152.76 | 68.06s |

```bash
cd examples/02_custom_model
python3 custom_yolo_inference.py
```

### Example 3: Multi-Object Tracking

Supports tracking algorithms including NvDCF, IOU, DeepSORT

```bash
cd examples/03_object_tracking
python3 tracking_demo.py
```

### Example 4: RTSP Multi-Stream Output

**Multi-Stream Performance Test** (3840×2160, YOLOv8n 640×640):

| Stream Count | GPU Usage | Status |
|-------------|-----------|--------|
| 4 streams | ~5% | ✅ Smooth |
| 8 streams | ~10% | ✅ Smooth |
| 12 streams | ~15% | ✅ Smooth |
| 16 streams | ~17% | ✅ Smooth |

```bash
cd examples/05_rtsp_multi_stream
python3 multi_stream_rtsp.py
```

View output via VLC or FFplay:
```bash
ffplay rtsp://localhost:8554/stream0
```

## 🐛 Common Issues

### Issue 1: VK_ERROR_INCOMPATIBLE_DRIVER

**Symptom**: Vulkan driver error at runtime, window fails to display

**Solutions**:
```python
# Method 1: Use fakesink (output detection results only)
sink = Gst.ElementFactory.make("fakesink", "fakesink")

# Method 2: Use filesink to save to file
sink = Gst.ElementFactory.make("filesink", "filesink")
sink.set_property("location", "output.mp4")
```

### Issue 2: GStreamer Plugin Loading Warnings

**Symptom**: Numerous `Failed to load plugin` warnings

**Note**: These warnings can be ignored and don't affect core functionality

### Issue 3: Cannot Display Window Inside Container

**Solution**:
```bash
# Execute on host machine
xhost +local:docker

# Ensure container starts with X11 parameters
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
```

More issues: [docs/en/troubleshooting.md](docs/en/troubleshooting.md)

## 📚 Related Resources

### Official Documentation
- [DeepStream SDK Developer Guide](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo) - YOLO model adaptation

### Reference Repositories
- [deepstream_reference_apps](https://github.com/NVIDIA-AI-IOT/deepstream_reference_apps) - C++ reference applications

## 💡 Why Choose Docker?

1. **Zero Risk** - Won't break host system environment
2. **Fully Reversible** - Simply delete container when not needed
3. **Consistent Environment** - DeepStream 8.0 requires Ubuntu 24.04, Docker runs on Ubuntu 22.04
4. **Good Isolation** - DeepStream configurations are system-level dependent, container issues don't affect external system

⚠️ **Note**: When deleting a container, all environments and installed packages within the container will be removed! It's recommended to mount important data to the host machine.

## 🤝 Contributing

Issues and Pull Requests are welcome!

If this project helps you, please give it a ⭐ Star!

## 📧 Contact

- **GitHub**: [@RuijieSpace](https://github.com/RuijieSpace)
- **Repository**: https://github.com/RuijieSpace/Deepstream_Python_Stack

## 📄 License

This project is licensed under the MIT License

---

<div align="center">

**Built with ❤️ by DeepStream Learners**

Feel free to open Issues for discussions!

</div>