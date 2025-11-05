# Deepstream_Python_Stack

<div align="center">

![DeepStream](https://img.shields.io/badge/DeepStream-8.0-76B900?style=flat-square&logo=nvidia)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

**DeepStream 8.0 Python Learning and Practice**

Documentation of problems, solutions, and practical code encountered during NVIDIA DeepStream Python development

English | [简体中文](README.md)

</div>

---

## 📖 Project Background

While learning from [NVIDIA-AI-IOT/deepstream_python_apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps) official examples, I found:

- ❌ Official repository has Issues disabled, making it difficult to discuss problems
- ❌ Extremely strict environment requirements (DeepStream 8.0 + Ubuntu 24.04)
- ❌ Lack of complete multi-stream multi-model inference examples
- ❌ Sample code mainly targets Jetson platform, requires extensive modifications for PC deployment
- ❌ Easy to encounter various environment configuration and runtime issues

Therefore, this repository was created to document practical experience with **Ubuntu 22.04 + DeepStream 8.0 + Docker** environment, helping developers facing similar challenges.

## ✨ Project Features

- ✅ **Docker container** based deployment, safe and reliable, fully reversible
- ✅ Detailed documentation of **complete process** from environment setup to execution
- ✅ Provides **ready-to-run** sample code and configurations
- ✅ Solves **common bugs** in official examples (e.g., Vulkan driver issues)
- ✅ Includes **multi-stream processing**, **custom models**, **RTSP output** and other practical scenarios
- ✅ Performance testing data and optimization recommendations
- ✅ **Complete Python Bindings (pyds) installation guide**
- ✅ **DeepStream-Yolo integration support**

## 🛠️ Environment Configuration

### System Requirements

| Item | Requirement |
|------|-------------|
| OS | Ubuntu 22.04 LTS |
| CUDA | 12.0+ / 13.0 |
| NVIDIA Driver | 525+ / 580+ |
| GPU | NVIDIA GPU (RTX 2060+ recommended) |
| VRAM | 4GB+ |
| RAM | 8GB+ |

### Verify System Environment

```bash
# Check system version
cat /etc/os-release

# Check NVIDIA driver
nvidia-smi

# Check CUDA version
nvidia-smi | grep "CUDA Version"
```

**Reference Configuration**:
- Operating System: Ubuntu 22.04
- CUDA Version: 13.0
- Driver Version: 580.65.06

### Core Dependencies

- **Docker** + **NVIDIA Container Toolkit**
- **DeepStream 8.0** (via Docker image)
- **Python 3.8+**
- **GStreamer 1.0**
- **Python Bindings (pyds)**

## 🚀 Complete Deployment Process

### Step 1: Install Docker

```bash
# 1. Remove old Docker versions (if any)
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null || true

# 2. Update package index
sudo apt update

# 3. Install dependencies
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 4. Add Docker official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 5. Setup Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# 7. Verify Docker installation
sudo docker run hello-world

# 8. Add current user to docker group (avoid using sudo every time)
sudo usermod -aG docker $USER

# 9. Reload user groups (important!)
newgrp docker

# 10. Verify again (without sudo)
docker run hello-world
```

### Step 2: Configure Docker Registry Mirrors

```bash
# 1. Create or edit Docker config file
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

Paste the following content:

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

Save and exit (`Ctrl+X`, `Y`, `Enter`)

```bash
# 2. Restart Docker service
sudo systemctl daemon-reload
sudo systemctl restart docker

# 3. Verify configuration
sudo docker info | grep -A 5 "Registry Mirrors"

# 4. Test
docker run hello-world
```

### Step 3: Install NVIDIA Container Toolkit

```bash
# 1. Add NVIDIA Container Toolkit repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Update package list
sudo apt update

# 3. Install NVIDIA Container Toolkit
sudo apt install -y nvidia-container-toolkit

# 4. Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# 5. Restart Docker service
sudo systemctl restart docker

# 6. Verify GPU is available in Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### Step 4: Pull DeepStream 8.0 Image

```bash
# Pull DeepStream 8.0 image (about 8GB, takes a few minutes)
docker pull nvcr.io/nvidia/deepstream:8.0-triton-multiarch

# If the above image is unavailable, try:
# docker pull nvcr.io/nvidia/deepstream:8.0-gc-triton-devel

# View images
docker images | grep deepstream
```

### Step 5: Create Working Directory

```bash
# Create project directory structure on host
mkdir -p ~/deepstream8_project
cd ~/deepstream8_project

# Create subdirectories
mkdir -p configs videos output scripts models

# View directory structure
tree -L 1  # or use ls -la
```

### Step 6: Configure X11 Display (Optional)

⚠️ **Note**: DeepStream is best suited for Nvidia Jetson platform, and may not display windows properly on PC. It's recommended to use RTSP protocol to stream video outside the container for viewing.

```bash
# Allow Docker container to access X11 display
xhost +local:docker

# If xhost command not found, install it:
# sudo apt install x11-xserver-utils
```

### Step 7: Start Container

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

**Parameter Explanation**:
- `--name`: Container name
- `--gpus all`: Use all GPUs
- `--network host`: Use host network (for RTSP streaming)
- `-e DISPLAY`: Pass display environment variable
- `-v`: Mount directory (host_path:container_path)

### Step 8: Configure Environment Inside Container

#### 8.1 Clone Project Repository

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/RuijieSpace/Deepstream_Python_Stack.git
cd Deepstream_Python_Stack
```

#### 8.2 Install System Dependencies

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

#### 8.3 Install Python Dependencies

```bash
pip3 install pybind11 numpy cuda-python
```

#### 8.4 Compile and Install Python Bindings (pyds)

```bash
# Enter DeepStream Python bindings source directory
cd /opt/nvidia/deepstream/deepstream/sources

# Initialize submodules
git submodule update --init --recursive

# Create build directory
cd bindings
rm -rf build && mkdir build && cd build

# Configure CMake (auto-detect Python version)
cmake .. \
    -DPYTHON_MAJOR_VERSION=3 \
    -DPYTHON_MINOR_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)

# Compile (use all CPU cores for speed)
make -j$(nproc)

# Verify generated file
ls -lh pyds.so
```

#### 8.5 Install pyds to Python Environment

```bash
# Get Python site-packages path
PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Python site-packages path: $PYTHON_SITE"

# Copy pyds.so to Python path
cp pyds.so "$PYTHON_SITE/"

# Verify installation
python3 -c "import pyds; print('✓ pyds imported successfully, version:', pyds.__version__)"
```

**Success Indicator**: You should see `✓ pyds imported successfully` message

#### 8.6 Install DeepStream-Yolo (Optional)

If you need to use YOLO models, install DeepStream-Yolo:

```bash
# Clone DeepStream-Yolo repository
cd /opt/nvidia/deepstream/deepstream/my_apps
git clone https://github.com/marcoslucianops/DeepStream-Yolo.git
cd DeepStream-Yolo

# Set CUDA version (choose according to DeepStream version)
export CUDA_VER=12.8  # DeepStream 8.0 corresponds to CUDA 12.8

# Compile custom YOLO plugin
make -C nvdsinfer_custom_impl_Yolo clean && \
make -C nvdsinfer_custom_impl_Yolo
```

**CUDA Version Reference Table**:
- DeepStream 8.0 = CUDA 12.8
- DeepStream 7.1 = CUDA 12.6
- DeepStream 7.0 / 6.4 = CUDA 12.2
- DeepStream 6.3 = CUDA 12.1
- DeepStream 6.2 = CUDA 11.8

### Step 9: Run Example Tests

#### Test 1: Official Model Detection

```bash
cd /opt/nvidia/deepstream/deepstream/my_apps/Deepstream_Python_Stack/examples/01_deepstream_test_1

python3 deepstream_test_1.py \
    /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264
```

**Expected Output**:

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

#### Test 2: View Saved Video

If you mounted the host directory, you can view the output video on the host:

```bash
# Execute on host
cd ~/deepstream8_project/test_data
ls -lh output_video.mp4
```

## 🗺️ Project Roadmap

### ✅ Completed

#### 1️⃣ Official Model Video Detection Test (Prevent Fake Video Input)
- [x] Basic video detection pipeline setup
- [x] ResNet-10 model integration
- [x] 4-class object detection (Vehicle, Person, Bicycle, Roadsign)
- [x] Solved Vulkan driver compatibility issues
- [x] Video file output functionality

#### 2️⃣ Custom Model Detection and Parallel Video Inference Test
- [x] YOLOv8 model adaptation
- [x] Custom model configuration file generation
- [x] Model performance testing (FPS statistics)
- [x] Multi-model parallel inference verification

#### 3️⃣ Add Tracking Module Testing
- [x] NvDCF tracker integration
- [x] IOU tracker support
- [x] Tracking configuration optimization

### 🚧 In Progress

#### 4️⃣ Single Video Stream Multi-Model Test (YAML Configuration)
- [x] 4.1 Serial Models
  - Multi-stage detection pipeline (e.g., Vehicle Detection → License Plate Recognition)
- [x] 4.2 Parallel Models
  - Multi-task parallel inference (e.g., Detection + Segmentation)
- [ ] 4.3 Serial vs Parallel Comparison
  - Performance comparison analysis report
  - Best practice recommendations

### 📋 Planned

#### 5️⃣ Multi-Stream Multi-Model
- [ ] 4.1 Serial Models
  - Serial processing for multi-input streams
- [ ] 4.2 Parallel Models
  - Parallel inference for multi-input streams
- [ ] 4.3 Different Sources Comparison
  - Local files vs RTSP stream performance comparison
  - Resource usage analysis

#### 6️⃣ RTSP Input/Output
- [ ] Multi-stream multi-model RTSP approach
  - Real-time video stream input
  - Multi-channel RTSP output
  - Low latency optimization

### 📊 Feature Completion Status

| Module | Status | Completion |
|--------|--------|------------|
| Environment Deployment | ✅ Completed | 100% |
| Official Model Test | ✅ Completed | 100% |
| Custom Model | ✅ Completed | 100% |
| Object Tracking | ✅ Completed | 100% |
| Single-Stream Multi-Model | 🚧 In Progress | 60% |
| Multi-Stream Multi-Model | 📋 Planned | 0% |
| Complete RTSP Solution | 📋 Planned | 30% |

## 📂 Project Structure

```
Deepstream_Python_Stack/
├── README.md                          # Project documentation
├── README_EN.md                       # English documentation
├── docs/                              # Detailed documentation
│   ├── installation.md                # Complete installation guide
│   ├── troubleshooting.md             # Troubleshooting manual
│   ├── performance_analysis.md        # Performance analysis report
│   └── api_reference.md               # API reference
├── examples/                          # Sample code
│   ├── 01_deepstream_test_1/          # Official model video test ✅
│   ├── 02_custom_model/               # Custom model inference ✅
│   ├── 03_object_tracking/            # Object tracking ✅
│   ├── 04_single_stream_multi_model/  # Single-stream multi-model 🚧
│   ├── 05_multi_stream_multi_model/   # Multi-stream multi-model 📋
│   └── 06_rtsp_full_solution/         # Complete RTSP solution 📋
├── configs/                           # Configuration files
│   ├── models/                        # Model configurations
│   ├── tracker/                       # Tracker configurations
│   └── yaml/                          # YAML configuration files 🚧
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

**Features**: Detect 4 object classes using ResNet-10 model (Vehicle, Person, Bicycle, Roadsign)

**Resolved Issues**:
- ❌ `VK_ERROR_INCOMPATIBLE_DRIVER` Vulkan driver incompatibility
- ✅ Use `fakesink` or modify to `filesink` output

```bash
cd examples/01_deepstream_test_1
python3 deepstream_test_1.py <video_file>
```

### Example 2: Custom YOLOv8 Model Inference

**Performance Data** (3840×2160 video, 12179 frames):

| Model | Input Size | Average FPS | Total Time |
|-------|------------|-------------|------------|
| YOLOv8n | 640×640 | 497.21 | 25.01s |
| Custom Person Model | 1920×1920 | 310.34 | 39.75s |
| Custom Highway Model | 1920×1920 | 152.76 | 68.06s |

```bash
cd examples/02_custom_model
python3 custom_yolo_inference.py
```

### Example 3: Multi-Object Tracking

Supports NvDCF, IOU, DeepSORT and other tracking algorithms

```bash
cd examples/03_object_tracking
python3 tracking_demo.py
```

### Example 4: RTSP Multi-Stream Output

**Multi-Stream Performance Test** (3840×2160, YOLOv8n 640×640):

| Stream Count | GPU Utilization | Status |
|--------------|-----------------|--------|
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

**Symptom**: Vulkan driver error at runtime, window cannot display

**Solution**:
```python
# Method 1: Use fakesink (detection results only)
sink = Gst.ElementFactory.make("fakesink", "fakesink")

# Method 2: Use filesink to save to file
sink = Gst.ElementFactory.make("filesink", "filesink")
sink.set_property("location", "output.mp4")

# Method 3: Use RTSP output (recommended)
# See examples 04 and 05
```

### Issue 2: pyds Import Failure

**Symptom**: `ImportError: No module named 'pyds'`

**Solution**:
```bash
# Check if pyds.so exists
python3 -c "import site; print(site.getsitepackages()[0])"
ls -l /usr/local/lib/python3.*/dist-packages/pyds.so

# Reinstall pyds
cd /opt/nvidia/deepstream/deepstream/sources/bindings/build
PYTHON_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
cp pyds.so "$PYTHON_SITE/"
```

### Issue 3: GStreamer Plugin Loading Warnings

**Symptom**: Many `Failed to load plugin` warnings

**Explanation**: These warnings can be ignored and don't affect core functionality. DeepStream attempts to load multiple optional plugins and produces warnings when not found.

### Issue 4: Cannot Display Window Inside Container

**Solution**:
```bash
# Execute on host
xhost +local:docker

# Ensure container startup includes X11 related parameters
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
```

**Recommended Solution**: Use RTSP protocol to stream video outside the container for viewing, avoiding X11 display issues.

### Issue 5: Environment Lost After Container Deletion

**Explanation**: This is normal Docker behavior. When deleting a container, all environments and installed packages inside the container are deleted.

**Solution**:
```bash
# Method 1: Don't use --rm parameter, keep container
docker run -it --name deepstream_python_stack ...

# Re-enter after stopping
docker start deepstream_python_stack
docker exec -it deepstream_python_stack /bin/bash

# Method 2: Mount important data to host
-v ~/deepstream8_project:/workspace

# Method 3: Create custom image to save environment
docker commit deepstream_python_stack my_deepstream:v1
```

For more issues, check: [docs/troubleshooting.md](docs/troubleshooting.md)

## 📚 Related Resources

### Official Documentation
- [DeepStream SDK Development Guide](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo) - YOLO model adaptation

### Reference Repositories
- [deepstream_reference_apps](https://github.com/NVIDIA-AI-IOT/deepstream_reference_apps) - C++ reference applications (production-level complete solution)

### Core Feature Comparison

| Repository | Language | Platform | Features |
|------------|----------|----------|----------|
| deepstream_python_apps | Python | Jetson/x86 | Official examples, need modification |
| DeepStream-Yolo | C++/Python | x86 | YOLO model adaptation, GPU post-processing optimization |
| deepstream_reference_apps | C++ | Jetson/x86 | Production-level solution, multi-model parallel |
| **This Project** | Python | x86 (Ubuntu 22.04) | Docker deployment, ready to use |

## 💡 Why Choose Docker?

### ✅ Advantages of Docker Solution

1. **Zero Risk** - Won't damage host system environment
2. **Fully Reversible** - Delete container when not needed
3. **Environment Consistency** - DeepStream 8.0 requires Ubuntu 24.04, Docker can run on Ubuntu 22.04
4. **Good Isolation** - DeepStream configurations are system-level related, container issues don't affect the outside
5. **Easy Distribution** - Can be packaged as an image for quick deployment on other machines

### ⚠️ Notes

- When deleting a container, all environments and installed packages inside the container will be deleted
- Recommend mounting important data and code to the host
- Use `docker commit` to save configured environment as a new image

## 🎯 Quick Command Reference

### Docker Container Management

```bash
# Start new container
docker run -it --rm --name deepstream8 --gpus all ...

# Stop container
docker stop deepstream8

# Start stopped container
docker start deepstream8

# Enter running container
docker exec -it deepstream8 /bin/bash

# List containers
docker ps -a

# Delete container
docker rm deepstream8

# Save container as image
docker commit deepstream8 my_deepstream:v1
```

### Common Verification Commands

```bash
# Verify GPU
nvidia-smi

# Verify DeepStream
deepstream-app --version

# Verify Python Bindings
python3 -c "import pyds; print(pyds.__version__)"

# View GStreamer plugins
gst-inspect-1.0 nvinfer
```

## 🤝 Contributing

Issues and Pull Requests are welcome!

If this project helps you, please give it a ⭐ Star!

### Contribution Guidelines

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📧 Contact

- **GitHub**: [@RuijieSpace](https://github.com/RuijieSpace)
- **Project URL**: https://github.com/RuijieSpace/Deepstream_Python_Stack

## 📄 License

This project is licensed under the MIT License

---

<div align="center">

**Built with ❤️ by DeepStream Learners**

If you encounter any issues, feel free to open an Issue!

[![GitHub stars](https://img.shields.io/github/stars/RuijieSpace/Deepstream_Python_Stack?style=social)](https://github.com/RuijieSpace/Deepstream_Python_Stack)
[![GitHub forks](https://img.shields.io/github/forks/RuijieSpace/Deepstream_Python_Stack?style=social)](https://github.com/RuijieSpace/Deepstream_Python_Stack)

</div>