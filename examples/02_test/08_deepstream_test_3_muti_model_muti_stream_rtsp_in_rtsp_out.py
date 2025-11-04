"""
DeepStream RTSP 输入输出完整方案（调试版本）
支持: RTSP 输入 → 多模型推理 → RTSP 输出
架构: rtspsrc → mux → models → tracker → tiler → nvosd → encoder → RTSP
"""

import sys
sys.path.append('../')
import os
import time
import yaml
import configparser
import math
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GLib, Gst, GstRtspServer
from common.bus_call import bus_call
import pyds

UNTRACKED_OBJECT_ID = 0xFFFFFFFFFFFFFFFF

# 全局变量
MODELS_CONFIG = None
TILER_ROWS = 1
TILER_COLS = 1
TILER_WIDTH = 1920
TILER_HEIGHT = 1080
stream_stats = {}
stream_ended = set()
active_streams = set()
debug_frame_count = {}  # 每个源的帧计数

# ==================== 加载配置 ====================
def load_config(config_file="models_config_rtsp_in_rtsp_out.yaml"):
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
    for encoding in encodings:
        try:
            with open(config_file, 'r', encoding=encoding) as f:
                config = yaml.safe_load(f)
            return config
        except:
            continue
    sys.exit(1)

# ==================== FPS 计算器 ====================
class FPSCalculator:
    def __init__(self):
        self.frame_timestamps = []
        self.fps = 0.0
        self.frame_count = 0
        self.start_time = None
        
    def update(self):
        if self.start_time is None:
            self.start_time = time.time()
        self.frame_count += 1
        current_time = time.time()
        self.frame_timestamps.append(current_time)
        if len(self.frame_timestamps) > 30:
            self.frame_timestamps.pop(0)
        if len(self.frame_timestamps) >= 2:
            time_diff = self.frame_timestamps[-1] - self.frame_timestamps[0]
            if time_diff > 0:
                self.fps = (len(self.frame_timestamps) - 1) / time_diff
        return self.fps
    
    def get_average_fps(self):
        if self.start_time and self.frame_count > 0:
            return self.frame_count / (time.time() - self.start_time)
        return 0.0

fps_calculator = FPSCalculator()

# ==================== Probe 0: Streammux 调试 ====================
def streammux_src_probe(pad, info, u_data):
    """检查 streammux 输出"""
    global debug_frame_count
    
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK
    
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    
    l_frame = batch_meta.frame_meta_list
    frame_count = 0
    source_ids = []
    
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            source_id = frame_meta.source_id
            source_ids.append(source_id)
            frame_count += 1
            
            if source_id not in debug_frame_count:
                debug_frame_count[source_id] = 0
            debug_frame_count[source_id] += 1
            
            l_frame = l_frame.next
        except StopIteration:
            break
    
    total_frames = sum(debug_frame_count.values())
    if total_frames % 30 == 0 and total_frames > 0:
        print(f"🔍 [Streammux] Batch: {frame_count} frames, Sources: {source_ids}, Total: {debug_frame_count}")
    
    return Gst.PadProbeReturn.OK

# ==================== Probe 1: 收集统计 ====================
def pre_tiler_probe(pad, info, u_data):
    """收集统计信息，设置边框和标签"""
    global stream_stats, active_streams
    
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    current_fps = fps_calculator.update()
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    
    stream_stats = {}
    current_active = set()
    
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        source_id = frame_meta.source_id
        current_active.add(source_id)
        
        model_counters = {}
        for model_cfg in MODELS_CONFIG['models']:
            model_id = model_cfg['id']
            model_counters[model_id] = {k: 0 for k in model_cfg['classes'].keys()}
        
        tracked_objects = set()
        display_tracking = MODELS_CONFIG.get('tracker', {}).get('display_tracking_id', True)
        
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            model_id = obj_meta.unique_component_id
            class_id = obj_meta.class_id
            object_id = obj_meta.object_id
            
            is_tracked = (object_id != UNTRACKED_OBJECT_ID)
            if is_tracked:
                tracked_objects.add(object_id)
            
            for model_cfg in MODELS_CONFIG['models']:
                if model_cfg['id'] == model_id:
                    if class_id in model_cfg['classes']:
                        model_counters[model_id][class_id] += 1
                        
                        color = model_cfg['color']
                        obj_meta.rect_params.border_color.set(
                            color['r'], color['g'], color['b'], 0.9
                        )
                        obj_meta.rect_params.border_width = model_cfg['border_width']
                        
                        class_name = model_cfg['classes'].get(class_id, 'unknown')
                        if display_tracking and is_tracked:
                            obj_meta.text_params.display_text = f"{class_name}[{object_id}]"
                        else:
                            obj_meta.text_params.display_text = f"{class_name}"
                        
                        obj_meta.text_params.x_offset = int(obj_meta.rect_params.left)
                        obj_meta.text_params.y_offset = max(0, int(obj_meta.rect_params.top) - 10)
                        obj_meta.text_params.font_params.font_name = "Serif"
                        obj_meta.text_params.font_params.font_size = 10
                        obj_meta.text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
                        obj_meta.text_params.set_bg_clr = 1
                        obj_meta.text_params.text_bg_clr.set(0.0, 0.0, 0.0, 0.7)
                    break
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        
        stream_stats[source_id] = {
            'frame_number': frame_number,
            'model_counters': model_counters,
            'tracked_objects': len(tracked_objects),
            'fps': current_fps
        }
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break
    
    active_streams = current_active
    
    if fps_calculator.frame_count % 30 == 0 and stream_stats:
        num_active = len(active_streams)
        num_ended = len(stream_ended)
        
        print(f"\n[Overall] FPS: {current_fps:5.1f} | Active: {num_active} | Ended: {num_ended} | Frames: {fps_calculator.frame_count}")
        
        for sid in sorted(stream_stats.keys()):
            stats = stream_stats[sid]
            stats_str = " | ".join([
                f"M{cfg['id']}:{sum(stats['model_counters'][cfg['id']].values()):2d}"
                for cfg in MODELS_CONFIG['models']
            ])
            status = "🔴ENDED" if sid in stream_ended else "🟢ACTIVE"
            print(f"  Stream-{sid:2d} {status} Frame {stats['frame_number']:4d}: {stats_str} | Tracked:{stats['tracked_objects']}")
        
        if num_ended > 0:
            ended_not_shown = stream_ended - set(stream_stats.keys())
            if ended_not_shown:
                print(f"  📊 Already ended: {sorted(ended_not_shown)}")
    
    return Gst.PadProbeReturn.OK

# ==================== Probe 2: 添加 OSD ====================
def nvosd_sink_pad_buffer_probe(pad, info, u_data):
    """添加统计信息到画面"""
    global stream_stats, TILER_ROWS, TILER_COLS, TILER_WIDTH, TILER_HEIGHT
    
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK
    
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    
    l_frame = batch_meta.frame_meta_list
    if not l_frame:
        return Gst.PadProbeReturn.OK
    
    try:
        frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
    except StopIteration:
        return Gst.PadProbeReturn.OK
    
    tile_width = TILER_WIDTH // TILER_COLS
    tile_height = TILER_HEIGHT // TILER_ROWS
    
    for source_id, stats in stream_stats.items():
        row = source_id // TILER_COLS
        col = source_id % TILER_COLS
        
        x_offset = col * tile_width + 10
        y_offset = row * tile_height + 12
        
        num_models = len(MODELS_CONFIG['models'])
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = num_models + 2
        
        params_fps = display_meta.text_params[0]
        mode_str = MODELS_CONFIG['pipeline']['mode'].upper()
        status = "ENDED" if source_id in stream_ended else "ACTIVE"
        params_fps.display_text = f"Stream-{source_id}[{status}]|{mode_str}|FPS:{stats['fps']:.1f}|F:{stats['frame_number']}"
        params_fps.x_offset = x_offset
        params_fps.y_offset = y_offset
        params_fps.font_params.font_name = "Serif"
        params_fps.font_params.font_size = 12
        
        if source_id in stream_ended:
            params_fps.font_params.font_color.set(1.0, 0.0, 0.0, 1.0)
        else:
            params_fps.font_params.font_color.set(1.0, 1.0, 0.0, 1.0)
        
        params_fps.set_bg_clr = 1
        params_fps.text_bg_clr.set(0.0, 0.0, 0.0, 0.9)
        
        for idx, model_cfg in enumerate(MODELS_CONFIG['models'], start=1):
            model_id = model_cfg['id']
            params = display_meta.text_params[idx]
            
            model_counters = stats['model_counters'][model_id]
            stat_list = [f"M{model_id}:"]
            for class_id, count in model_counters.items():
                if count > 0:
                    class_name = model_cfg['classes'][class_id]
                    stat_list.append(f"{class_name}={count}")
            
            params.display_text = " ".join(stat_list) if len(stat_list) > 1 else f"M{model_id}:0"
            params.x_offset = x_offset
            params.y_offset = y_offset + idx * 20
            params.font_params.font_name = "Serif"
            params.font_params.font_size = 10
            
            color = model_cfg['color']
            params.font_params.font_color.set(color['r'], color['g'], color['b'], 1.0)
            params.set_bg_clr = 1
            params.text_bg_clr.set(0.0, 0.0, 0.0, 0.8)
        
        if MODELS_CONFIG.get('tracker', {}).get('enable'):
            params_track = display_meta.text_params[num_models + 1]
            params_track.display_text = f"Tracked:{stats['tracked_objects']}"
            params_track.x_offset = x_offset
            params_track.y_offset = y_offset + (num_models + 1) * 20
            params_track.font_params.font_name = "Serif"
            params_track.font_params.font_size = 10
            params_track.font_params.font_color.set(0.0, 1.0, 1.0, 1.0)
            params_track.set_bg_clr = 1
            params_track.text_bg_clr.set(0.0, 0.0, 0.0, 0.8)
        
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
    
    return Gst.PadProbeReturn.OK

# # ==================== 创建 RTSP 输入源 ====================
# def create_rtsp_source_bin(index, rtsp_uri):
#     """创建 RTSP 输入源（带详细调试）"""
#     bin_name = f"rtsp-source-bin-{index:02d}"
#     nbin = Gst.Bin.new(bin_name)
    
#     source = Gst.ElementFactory.make("rtspsrc", f"rtsp-source-{index}")
#     depay = Gst.ElementFactory.make("rtph264depay", f"depay-{index}")
#     parser = Gst.ElementFactory.make("h264parse", f"parser-{index}")
#     decoder = Gst.ElementFactory.make("nvv4l2decoder", f"decoder-{index}")
#     nvvidconv = Gst.ElementFactory.make("nvvideoconvert", f"convertor-{index}")
#     capsfilter = Gst.ElementFactory.make("capsfilter", f"caps-{index}")
    
#     if not all([source, depay, parser, decoder, nvvidconv, capsfilter]):
#         print(f"❌ Error: Failed to create elements for stream {index}")
#         return None
    
#     # 配置 rtspsrc
#     source.set_property('location', rtsp_uri)
#     source.set_property('latency', 100)
#     source.set_property('retry', 10)
#     source.set_property('timeout', 5000000)
#     source.set_property('drop-on-latency', True)
#     source.set_property('protocols', 'tcp')
#     source.set_property('do-rtcp', True)
    
#     caps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=NV12")
#     capsfilter.set_property("caps", caps)
    
#     nbin.add(source)
#     nbin.add(depay)
#     nbin.add(parser)
#     nbin.add(decoder)
#     nbin.add(nvvidconv)
#     nbin.add(capsfilter)
    
#     # 动态连接 rtspsrc 的 pad（修复版本）
#     def on_pad_added(element, pad):
#         caps = pad.get_current_caps()
#         if caps:
#             structure = caps.get_structure(0)
#             name = structure.get_name()
#             print(f"🔍 Stream-{index}: rtspsrc pad-added, caps={name}")
#             if name.startswith("application/x-rtp"):
#                 sink_pad = depay.get_static_pad("sink")
#                 if not sink_pad.is_linked():
#                     result = pad.link(sink_pad)
#                     if result == Gst.PadLinkReturn.OK:
#                         print(f"✅ Stream-{index}: rtspsrc → depay linked successfully")
#                     else:
#                         print(f"❌ Stream-{index}: Link failed: {result.value_name}")
#                 else:
#                     print(f"⚠️  Stream-{index}: depay sink pad already linked")
    
#     source.connect("pad-added", on_pad_added)
    
#     # 静态连接其他元素
#     if not depay.link(parser):
#         print(f"❌ Stream-{index}: Failed to link depay → parser")
#         return None
#     if not parser.link(decoder):
#         print(f"❌ Stream-{index}: Failed to link parser → decoder")
#         return None
#     if not decoder.link(nvvidconv):
#         print(f"❌ Stream-{index}: Failed to link decoder → nvvidconv")
#         return None
#     if not nvvidconv.link(capsfilter):
#         print(f"❌ Stream-{index}: Failed to link nvvidconv → capsfilter")
#         return None
    
#     print(f"  [OK] Stream-{index}: Static elements linked")
    
#     # 创建 ghost pad
#     srcpad = capsfilter.get_static_pad("src")
#     ghost_pad = Gst.GhostPad.new("src", srcpad)
#     nbin.add_pad(ghost_pad)
    
#     print(f"✅ Stream-{index}: Source bin created for {rtsp_uri}")
    
#     return nbin

def create_source_bin(index, uri):
    """使用 uridecodebin（参考官方）"""
    bin_name = f"source-bin-{index:02d}"
    nbin = Gst.Bin.new(bin_name)
    
    # 使用 uridecodebin（官方方式）
    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", f"uri-decode-bin-{index}")
    if not uri_decode_bin:
        print(f"❌ Unable to create uri decode bin for stream {index}")
        return None
    
    uri_decode_bin.set_property("uri", uri)
    
    # 动态连接回调
    def cb_newpad(decodebin, decoder_src_pad, data):
        print(f"🔍 Stream-{index}: uridecodebin pad-added")
        caps = decoder_src_pad.get_current_caps()
        gststruct = caps.get_structure(0)
        gstname = gststruct.get_name()
        features = caps.get_features(0)
        
        print(f"   caps name: {gstname}, features: {features}")
        
        # 只处理视频
        if gstname.find("video") != -1:
            # 检查是否使用了 NVIDIA decoder (NVMM)
            if features.contains("memory:NVMM"):
                bin_ghost_pad = nbin.get_static_pad("src")
                if not bin_ghost_pad.set_target(decoder_src_pad):
                    print(f"❌ Stream-{index}: Failed to link decoder to ghost pad")
                else:
                    print(f"✅ Stream-{index}: uridecodebin → ghost pad linked")
            else:
                print(f"❌ Stream-{index}: Decodebin did not pick nvidia decoder")
    
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    
    # ⭐ 关键：如果是 RTSP，配置 NTP 同步
    def decodebin_child_added(child_proxy, Object, name, user_data):
        print(f"🔍 Stream-{index}: uridecodebin child added: {name}")
        if name.find("decodebin") != -1:
            Object.connect("child-added", decodebin_child_added, user_data)
        # ⭐ 配置 RTSP source 的 NTP 同步
        if name.find("source") != -1 and uri.startswith("rtsp://"):
            try:
                pyds.configure_source_for_ntp_sync(hash(Object))
                print(f"  ✅ Stream-{index}: Configured NTP sync for RTSP")
            except:
                pass
    
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)
    
    Gst.Bin.add(nbin, uri_decode_bin)
    
    # 创建 ghost pad
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        print(f"❌ Stream-{index}: Failed to add ghost pad")
        return None
    
    print(f"✅ Stream-{index}: Source bin created (uridecodebin)")
    return nbin

# ==================== Bus Call ====================
def custom_bus_call(bus, message, loop, total_sources):
    """处理总线消息（带详细调试）"""
    global stream_ended
    
    t = message.type
    
    if t == Gst.MessageType.EOS:
        print("\n[INFO] ✅ Pipeline received EOS")
        loop.quit()
        
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        err_str = str(err)
        if "QoS" not in err_str and "upstream" not in err_str:
            sys.stderr.write(f"⚠️  Warning from {message.src.get_name()}: {err}\n")
        
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write(f"❌ Error from {message.src.get_name()}: {err}\n")
        sys.stderr.write(f"   Debug: {debug}\n")
        loop.quit()
    
    elif t == Gst.MessageType.ELEMENT:
        struct = message.get_structure()
        if struct and struct.get_name() == "stream-eos":
            try:
                if struct.has_field("source-id"):
                    source_id = struct.get_value("source-id")
                    stream_ended.add(source_id)
                    print(f"✅ Stream-{source_id} ended ({len(stream_ended)}/{total_sources})")
            except Exception as e:
                pass
    
    elif t == Gst.MessageType.STATE_CHANGED:
        if message.src.get_name().startswith("rtsp-source"):
            old, new, pending = message.parse_state_changed()
            if new == Gst.State.PLAYING:
                print(f"🔄 {message.src.get_name()}: {old.value_nick} → {new.value_nick}")
    
    return True

# ==================== 主函数 ====================
def main(args):
    global MODELS_CONFIG, TILER_ROWS, TILER_COLS, TILER_WIDTH, TILER_HEIGHT, active_streams
    
    if len(args) < 2:
        sys.stderr.write("usage: %s <rtsp://uri1> <rtsp://uri2> ... [config.yaml]\n" % args[0])
        sys.stderr.write("example: %s rtsp://localhost:8554/stream0 rtsp://localhost:8554/stream1 models_config_rtsp_in_rtsp_out.yaml\n" % args[0])
        sys.exit(1)

    rtsp_uris = []
    config_file = "models_config_rtsp_in_rtsp_out.yaml"
    
    for arg in args[1:]:
        if arg.endswith('.yaml'):
            config_file = arg
        elif arg.startswith('rtsp://') or arg.startswith('rtmp://'):
            rtsp_uris.append(arg)
        else:
            print(f"⚠️  Warning: Ignoring invalid URI: {arg}")
    
    if not rtsp_uris:
        sys.stderr.write("❌ ERROR: No RTSP URIs provided\n")
        sys.exit(1)
    
    num_sources = len(rtsp_uris)
    MODELS_CONFIG = load_config(config_file)
    active_streams = set(range(num_sources))
    
    Gst.init(None)

    mode = MODELS_CONFIG['pipeline']['mode']
    tracker_enabled = MODELS_CONFIG.get('tracker', {}).get('enable', False)
    use_fakesink = MODELS_CONFIG['pipeline'].get('debug', {}).get('use_fakesink', False)
    
    print("\n" + "="*80)
    print(f"DeepStream RTSP Input/Output {' (DEBUG MODE)' if use_fakesink else ''}")
    print(f"{num_sources} RTSP streams | {mode.upper()} | {'TRACKER' if tracker_enabled else 'NO TRACKER'}")
    print("="*80)
    for i, uri in enumerate(rtsp_uris):
        print(f"  Stream-{i}: {uri}")
    print("="*80)
    
    pipeline = Gst.Pipeline()
    
    # ==================== 创建元素 ====================
    streammux = Gst.ElementFactory.make("nvstreammux", "muxer")
    
    tracker = None
    if tracker_enabled:
        tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "tiler")
    nvosd = Gst.ElementFactory.make("nvdsosd", "osd")
    
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
    
    if use_fakesink:
        print("⚠️  DEBUG MODE: Using fakesink instead of RTSP output")
        sink = Gst.ElementFactory.make("fakesink", "fakesink")
        sink.set_property('sync', 0)
        sink.set_property('async', False)
        sink.set_property('silent', True)
        encoder = None
        h264parser = None
        rtppay = None
    else:
        encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
        h264parser = Gst.ElementFactory.make("h264parse", "h264parser")
        rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
        sink = Gst.ElementFactory.make("udpsink", "udpsink")
        
        rtppay.set_property('config-interval', 1)
        rtppay.set_property('pt', 96)
        
        output_cfg = MODELS_CONFIG['pipeline']['output']['rtsp']
        sink.set_property('host', output_cfg['multicast_ip'])
        sink.set_property('port', output_cfg['udp_port'])
        sink.set_property('async', False)
        sink.set_property('sync', 0)
        sink.set_property('qos', False)
    
    # ==================== 创建模型 ====================
    print(f"\n⚙️  Creating {len(MODELS_CONFIG['models'])} models in {mode} mode")
    
    model_elements = []
    queue_cfg = MODELS_CONFIG['pipeline'].get('queue', {})
    
    if mode == 'parallel':
        tee = Gst.ElementFactory.make("tee", "tee")
        metamux = Gst.ElementFactory.make("nvdsmetamux", "metamux")
        
        tee.set_property('allow-not-linked', True)
        
        for model_cfg in MODELS_CONFIG['models']:
            model_id = model_cfg['id']
            queue = Gst.ElementFactory.make("queue", f"queue{model_id}")
            pgie = Gst.ElementFactory.make("nvinfer", f"pgie{model_id}")
            
            max_buffers = queue_cfg.get('max_size_buffers', 3)
            leaky_mode = queue_cfg.get('leaky', 2)
            
            queue.set_property('max-size-buffers', max_buffers)
            queue.set_property('max-size-time', 0)
            queue.set_property('max-size-bytes', 0)
            queue.set_property('leaky', leaky_mode)
            queue.set_property('silent', True)
            queue.set_property('flush-on-eos', True)
            
            pgie.set_property('config-file-path', model_cfg['config'])
            pgie.set_property('unique-id', model_id)
            pgie.set_property('batch-size', num_sources)
            
            print(f"  [OK] Model-{model_id} batch={num_sources}")
            
            model_elements.append({'id': model_id, 'queue': queue, 'pgie': pgie})
        
        base_elements = [streammux, tee, metamux, tiler, nvosd, nvvidconv, capsfilter]
        if not use_fakesink:
            base_elements.extend([encoder, h264parser, rtppay])
        base_elements.append(sink)
    else:  # serial
        for model_cfg in MODELS_CONFIG['models']:
            model_id = model_cfg['id']
            pgie = Gst.ElementFactory.make("nvinfer", f"pgie{model_id}")
            
            pgie.set_property('config-file-path', model_cfg['config'])
            pgie.set_property('unique-id', model_id)
            pgie.set_property('batch-size', num_sources)
            
            print(f"  [OK] Model-{model_id} batch={num_sources}")
            
            model_elements.append({'id': model_id, 'pgie': pgie})
        
        base_elements = [streammux, tiler, nvosd, nvvidconv, capsfilter]
        if not use_fakesink:
            base_elements.extend([encoder, h264parser, rtppay])
        base_elements.append(sink)
    
    if tracker:
        tiler_idx = base_elements.index(tiler)
        base_elements.insert(tiler_idx, tracker)
    
    all_elements = base_elements.copy()
    for elem_dict in model_elements:
        all_elements.extend([v for k, v in elem_dict.items() if k != 'id'])
    
    # ==================== 配置 ====================
    mux_cfg = MODELS_CONFIG['pipeline']['streammux']
    streammux.set_property('batch-size', num_sources)
    streammux.set_property('width', mux_cfg['width'])
    streammux.set_property('height', mux_cfg['height'])
    streammux.set_property('batched-push-timeout', 40000)
    streammux.set_property('live-source', 1)
    
    try:
        streammux.set_property('sync-inputs', 0)
        print("  [OK] streammux: sync-inputs=0")
    except:
        pass
    
    # Tiler
    if num_sources == 1:
        rows, cols = 1, 1
    elif num_sources == 2:
        rows, cols = 1, 2
    elif num_sources <= 4:
        rows, cols = 2, 2
    elif num_sources <= 6:
        rows, cols = 2, 3
    elif num_sources <= 9:
        rows, cols = 3, 3
    elif num_sources <= 16:
        rows, cols = 4, 4
    else:
        rows = int(math.ceil(math.sqrt(num_sources)))
        cols = int(math.ceil(num_sources / rows))
    
    TILER_ROWS = rows
    TILER_COLS = cols
    TILER_WIDTH = 1920
    TILER_HEIGHT = 1080
    
    tiler.set_property('rows', rows)
    tiler.set_property('columns', cols)
    tiler.set_property('width', TILER_WIDTH)
    tiler.set_property('height', TILER_HEIGHT)
    
    print(f"  [OK] Tiler: {rows}x{cols} grid")
    
    if tracker:
        tracker_cfg = MODELS_CONFIG['tracker']
        if 'config_file' in tracker_cfg and os.path.exists(tracker_cfg['config_file']):
            config = configparser.ConfigParser()
            config.read(tracker_cfg['config_file'])
            for key in config['tracker']:
                if key == 'tracker-width':
                    tracker.set_property('tracker-width', config.getint('tracker', key))
                elif key == 'tracker-height':
                    tracker.set_property('tracker-height', config.getint('tracker', key))
                elif key == 'gpu-id':
                    tracker.set_property('gpu_id', config.getint('tracker', key))
                elif key == 'll-lib-file':
                    tracker.set_property('ll-lib-file', config.get('tracker', key))
                elif key == 'll-config-file':
                    tracker.set_property('ll-config-file', config.get('tracker', key))
    
    caps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420")
    capsfilter.set_property("caps", caps)
    
    if not use_fakesink:
        encoder.set_property("bitrate", MODELS_CONFIG['pipeline']['encoder']['bitrate'])
    
    # ==================== 添加到 pipeline ====================
    for elem in all_elements:
        pipeline.add(elem)
    
    # 创建 RTSP 源
    print("\n⚙️  Creating RTSP source bins...")
    for i, rtsp_uri in enumerate(rtsp_uris):
        source_bin = create_source_bin(i, rtsp_uri)
        if not source_bin:
            print(f"❌ Failed to create source bin for stream {i}")
            continue
        
        pipeline.add(source_bin)
        srcpad = source_bin.get_static_pad("src")
        sinkpad = streammux.request_pad_simple(f"sink_{i}")
        if srcpad.link(sinkpad) == Gst.PadLinkReturn.OK:
            print(f"  [OK] RTSP Source-{i} → streammux.sink_{i}")
        else:
            print(f"  ❌ Failed to link RTSP Source-{i} to streammux")
    
    # ==================== 链接 pipeline ====================
    print("\n⚙️  Linking pipeline elements...")
    if mode == 'parallel':
        streammux.link(tee)
        for idx, elem_dict in enumerate(model_elements):
            tee_src = tee.request_pad_simple(f"src_{idx}")
            queue_sink = elem_dict['queue'].get_static_pad("sink")
            tee_src.link(queue_sink)
            elem_dict['queue'].link(elem_dict['pgie'])
            pgie_src = elem_dict['pgie'].get_static_pad("src")
            metamux_sink = metamux.request_pad_simple(f"sink_{idx}")
            pgie_src.link(metamux_sink)
        
        if tracker:
            metamux.link(tracker)
            tracker.link(tiler)
        else:
            metamux.link(tiler)
    else:  # serial
        prev_elem = streammux
        for elem_dict in model_elements:
            prev_elem.link(elem_dict['pgie'])
            prev_elem = elem_dict['pgie']
        
        if tracker:
            prev_elem.link(tracker)
            tracker.link(tiler)
        else:
            prev_elem.link(tiler)
    
    tiler.link(nvosd)
    nvosd.link(nvvidconv)
    nvvidconv.link(capsfilter)
    
    if use_fakesink:
        capsfilter.link(sink)
    else:
        capsfilter.link(encoder)
        encoder.link(h264parser)
        h264parser.link(rtppay)
        rtppay.link(sink)
    
    print("  [OK] Pipeline linked")
    
    # ==================== 添加 Probes ====================
    print("\n⚙️  Adding probes...")
    
    # Probe 0: streammux 输出（调试用）
    streammux_srcpad = streammux.get_static_pad("src")
    streammux_srcpad.add_probe(Gst.PadProbeType.BUFFER, streammux_src_probe, 0)
    print("  [OK] Probe 0: streammux.src (DEBUG)")
    
    # Probe 1: 检测统计
    if tracker:
        probe_pad = tracker.get_static_pad("src")
        print("  [OK] Probe 1: tracker.src")
    elif mode == 'parallel':
        probe_pad = metamux.get_static_pad("src")
        print("  [OK] Probe 1: metamux.src")
    else:
        last_pgie = model_elements[-1]['pgie']
        probe_pad = last_pgie.get_static_pad("src")
        print("  [OK] Probe 1: last_pgie.src")
    
    probe_pad.add_probe(Gst.PadProbeType.BUFFER, pre_tiler_probe, 0)
    
    # Probe 2: OSD
    nvosd_sinkpad = nvosd.get_static_pad("sink")
    nvosd_sinkpad.add_probe(Gst.PadProbeType.BUFFER, nvosd_sink_pad_buffer_probe, 0)
    print("  [OK] Probe 2: nvosd.sink")
    
    # ==================== RTSP Server ====================
    if not use_fakesink:
        rtsp_cfg = MODELS_CONFIG['pipeline']['output']['rtsp']
        server = GstRtspServer.RTSPServer.new()
        server.props.service = "%d" % rtsp_cfg['rtsp_port']
        server.attach(None)
        
        factory = GstRtspServer.RTSPMediaFactory.new()
        factory.set_launch(
            "( udpsrc name=pay0 port=%d buffer-size=524288 "
            "caps=\"application/x-rtp, media=video, clock-rate=90000, "
            "encoding-name=(string)H264, payload=96\" )" % rtsp_cfg['udp_port']
        )
        factory.set_shared(True)
        server.get_mount_points().add_factory(rtsp_cfg['stream_path'], factory)
        
        print(f"\n📡 RTSP Output: rtsp://localhost:{rtsp_cfg['rtsp_port']}{rtsp_cfg['stream_path']}")
    else:
        print(f"\n⚠️  DEBUG MODE: No RTSP output, using fakesink")
    
    print("="*80 + "\n")
    
    # ==================== 运行 ====================
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", custom_bus_call, loop, num_sources)
    
    print("🚀 Starting pipeline...")
    print("="*80 + "\n")
    
    start_time = time.time()
    ret = pipeline.set_state(Gst.State.PLAYING)
    
    if ret == Gst.StateChangeReturn.FAILURE:
        print("❌ Unable to set pipeline to PLAYING state")
        sys.exit(1)
    
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
    
    pipeline.set_state(Gst.State.NULL)
    total_time = time.time() - start_time
    avg_fps = fps_calculator.get_average_fps()
    
    print("\n" + "="*80)
    print(f"✅ Completed: {total_time:.2f}s | {fps_calculator.frame_count} frames | {avg_fps:.2f} FPS")
    print(f"📊 Streams ended: {len(stream_ended)}/{num_sources}")
    print(f"📊 Debug frame count: {debug_frame_count}")
    print("="*80 + "\n")

if __name__ == '__main__':
    sys.exit(main(sys.argv))