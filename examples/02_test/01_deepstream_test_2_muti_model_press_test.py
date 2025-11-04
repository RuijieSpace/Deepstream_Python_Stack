#!/usr/bin/env python3

"""
DeepStream 8.0 三模型并行推理 - 支持多种视频编码格式
自动检测 H.264/H.265 并使用对应的 parser
"""

import sys
sys.path.append('../')
import os
import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst
from common.bus_call import bus_call
import pyds

MODEL1_CLASSES = {0: 'excavator', 1: 'pile_driver', 2: 'vehicle', 3: 'material'}
MODEL2_CLASSES = {0: 'person'}
MODEL3_CLASSES = {
    0: 'awning-tricycle', 1: 'bicycle', 2: 'bus', 3: 'car', 4: 'motor',
    5: 'pedestrian', 6: 'people', 7: 'tricycle', 8: 'truck', 9: 'van'
}

MUXER_BATCH_TIMEOUT_USEC = 33000
OUTPUT_VIDEO_PATH = "/workspace/3models_parallel_output.mp4"

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

def osd_sink_pad_buffer_probe(pad, info, u_data):
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    current_fps = fps_calculator.update()
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        model1_counter = {k: 0 for k in MODEL1_CLASSES.keys()}
        model2_counter = {k: 0 for k in MODEL2_CLASSES.keys()}
        model3_counter = {k: 0 for k in MODEL3_CLASSES.keys()}
        
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            
            model_id = obj_meta.unique_component_id
            class_id = obj_meta.class_id
            
            if model_id == 1 and class_id in model1_counter:
                model1_counter[class_id] += 1
                obj_meta.rect_params.border_color.set(1.0, 0.0, 0.0, 0.9)
                obj_meta.rect_params.border_width = 4
            elif model_id == 2 and class_id in model2_counter:
                model2_counter[class_id] += 1
                obj_meta.rect_params.border_color.set(0.0, 1.0, 0.0, 0.9)
                obj_meta.rect_params.border_width = 3
            elif model_id == 3 and class_id in model3_counter:
                model3_counter[class_id] += 1
                obj_meta.rect_params.border_color.set(0.0, 0.5, 1.0, 0.9)
                obj_meta.rect_params.border_width = 3
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 4
        
        params_fps = display_meta.text_params[0]
        params_fps.display_text = f"PARALLEL-3M | FPS: {current_fps:.1f} | Frame: {frame_number}"
        params_fps.x_offset = 10
        params_fps.y_offset = 12
        params_fps.font_params.font_name = "Serif"
        params_fps.font_params.font_size = 16
        params_fps.font_params.font_color.set(0.0, 1.0, 0.0, 1.0)
        params_fps.set_bg_clr = 1
        params_fps.text_bg_clr.set(0.0, 0.0, 0.0, 0.9)
        
        params1 = display_meta.text_params[1]
        stats1 = ["M1:"] + [f"{MODEL1_CLASSES[k]}={v}" for k, v in model1_counter.items() if v > 0]
        params1.display_text = " ".join(stats1) if len(stats1) > 1 else "M1: None"
        params1.x_offset = 10
        params1.y_offset = 44
        params1.font_params.font_name = "Serif"
        params1.font_params.font_size = 13
        params1.font_params.font_color.set(1.0, 0.0, 0.0, 1.0)
        params1.set_bg_clr = 1
        params1.text_bg_clr.set(0.0, 0.0, 0.0, 0.8)
        
        params2 = display_meta.text_params[2]
        stats2 = ["M2:"] + [f"{MODEL2_CLASSES[k]}={v}" for k, v in model2_counter.items() if v > 0]
        params2.display_text = " ".join(stats2) if len(stats2) > 1 else "M2: None"
        params2.x_offset = 10
        params2.y_offset = 72
        params2.font_params.font_name = "Serif"
        params2.font_params.font_size = 13
        params2.font_params.font_color.set(0.0, 1.0, 0.0, 1.0)
        params2.set_bg_clr = 1
        params2.text_bg_clr.set(0.0, 0.0, 0.0, 0.8)
        
        params3 = display_meta.text_params[3]
        stats3 = ["M3:"] + [f"{MODEL3_CLASSES[k]}={v}" for k, v in model3_counter.items() if v > 0]
        params3.display_text = " ".join(stats3) if len(stats3) > 1 else "M3: None"
        params3.x_offset = 10
        params3.y_offset = 100
        params3.font_params.font_name = "Serif"
        params3.font_params.font_size = 13
        params3.font_params.font_color.set(0.0, 0.5, 1.0, 1.0)
        params3.set_bg_clr = 1
        params3.text_bg_clr.set(0.0, 0.0, 0.0, 0.8)
        
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
        if frame_number % 30 == 0:
            m1 = sum(model1_counter.values())
            m2 = sum(model2_counter.values())
            m3 = sum(model3_counter.values())
            print(f"[PARALLEL] Frame {frame_number:4d} | FPS: {current_fps:5.1f} | M1:{m1:2d} M2:{m2:2d} M3:{m3:2d}")
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break
            
    return Gst.PadProbeReturn.OK


def main(args):
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file>\n" % args[0])
        sys.exit(1)

    Gst.init(None)

    print("\n" + "="*80)
    print("DeepStream 8.0 - 3-Model PARALLEL Inference (Multi-Format)")
    print("="*80)
    
    pipeline = Gst.Pipeline()
    
    # ==================== 创建元素 ====================
    source = Gst.ElementFactory.make("filesrc", "file-source")
    qtdemux = Gst.ElementFactory.make("qtdemux", "qt-demuxer")
    
    # ⭐ 注意：不在这里创建 parser，在 pad-added 回调中动态创建
    # 这样可以根据视频编码格式选择正确的 parser
    
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    
    # 并行架构
    tee = Gst.ElementFactory.make("tee", "tee")
    queue1 = Gst.ElementFactory.make("queue", "queue1")
    pgie1 = Gst.ElementFactory.make("nvinfer", "primary-inference-1")
    queue2 = Gst.ElementFactory.make("queue", "queue2")
    pgie2 = Gst.ElementFactory.make("nvinfer", "primary-inference-2")
    queue3 = Gst.ElementFactory.make("queue", "queue3")
    pgie3 = Gst.ElementFactory.make("nvinfer", "primary-inference-3")
    metamux = Gst.ElementFactory.make("nvdsmetamux", "metamux")
    
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    h264parser_enc = Gst.ElementFactory.make("h264parse", "h264-parser-enc")
    qtmux = Gst.ElementFactory.make("qtmux", "mux")
    sink = Gst.ElementFactory.make("filesink", "filesink")
    
    if not all([source, qtdemux, decoder, streammux, tee,
                queue1, pgie1, queue2, pgie2, queue3, pgie3, metamux,
                nvosd, nvvidconv, capsfilter, encoder, h264parser_enc, qtmux, sink]):
        sys.stderr.write("Failed to create elements\n")
        sys.exit(1)

    print("  [OK] All elements created")

    # ==================== 配置 ====================
    source.set_property('location', args[1])
    
    if os.environ.get('USE_NEW_NVSTREAMMUX') != 'yes':
        streammux.set_property('width', 1920)
        streammux.set_property('height', 1080)
        streammux.set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
    streammux.set_property('batch-size', 1)
    
    pgie1.set_property('config-file-path', "dstest2_pgie_1_config.txt")
    pgie1.set_property('unique-id', 1)
    pgie2.set_property('config-file-path', "dstest2_pgie_2_config.txt")
    pgie2.set_property('unique-id', 2)
    pgie3.set_property('config-file-path', "dstest2_pgie_3_config.txt")
    pgie3.set_property('unique-id', 3)
    
    for q in [queue1, queue2, queue3]:
        q.set_property('max-size-buffers', 2)
    
    caps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420")
    capsfilter.set_property("caps", caps)
    encoder.set_property("bitrate", 4000000)
    sink.set_property("location", OUTPUT_VIDEO_PATH)
    sink.set_property("sync", 0)
    sink.set_property("async", 0)

    print(f"\nConfiguration:")
    print(f"  Input: {args[1]}")
    print(f"  Output: {OUTPUT_VIDEO_PATH}")
    print(f"  Mode: PARALLEL with auto-format detection\n")

    # ==================== 添加到 pipeline ====================
    # 注意：parser 会在 pad-added 回调中动态添加
    for elem in [source, qtdemux, decoder, streammux, tee,
                 queue1, pgie1, queue2, pgie2, queue3, pgie3, metamux,
                 nvosd, nvvidconv, capsfilter, encoder, h264parser_enc, qtmux, sink]:
        pipeline.add(elem)

    print("  [OK] Elements added to pipeline")

    # ==================== 链接（带自动格式检测）====================
    source.link(qtdemux)
    print("  [OK] source -> qtdemux")
    
    # ⭐ 关键：动态检测并链接
    def qtdemux_pad_added(demux, src_pad):
        """改进版：自动检测视频编码格式"""
        
        # 1. 获取 caps
        caps = src_pad.get_current_caps()
        if not caps:
            print("  [ERROR] No caps from qtdemux")
            return
        
        structure = caps.get_structure(0)
        stream_name = structure.get_name()
        
        print(f"\n  [INFO] Detected stream: {stream_name}")
        
        # 2. 只处理视频流
        if not stream_name.startswith("video"):
            print(f"  [SKIP] Not a video stream")
            return
        
        # 3. 根据编码格式选择 parser
        parser = None
        parser_name = None
        
        if "h264" in stream_name.lower() or "avc" in stream_name.lower():
            parser = Gst.ElementFactory.make("h264parse", "h264-parser")
            parser_name = "h264parse"
            print(f"  [OK] Video format: H.264 (AVC)")
            
        elif "h265" in stream_name.lower() or "hevc" in stream_name.lower():
            parser = Gst.ElementFactory.make("h265parse", "h265-parser")
            parser_name = "h265parse"
            print(f"  [OK] Video format: H.265 (HEVC)")
            
        else:
            print(f"  [ERROR] Unsupported video format: {stream_name}")
            print(f"  [HINT] Supported formats: H.264, H.265")
            return
        
        # 4. 检查 parser 创建是否成功
        if not parser:
            print(f"  [ERROR] Failed to create {parser_name}")
            return
        
        # 5. 添加 parser 到 pipeline
        pipeline.add(parser)
        parser.sync_state_with_parent()
        print(f"  [OK] Added {parser_name} to pipeline")
        
        # 6. 获取 parser 的 sink pad
        parser_sink = parser.get_static_pad("sink")
        if not parser_sink:
            print(f"  [ERROR] Cannot get sink pad from {parser_name}")
            return
        
        # 7. 检查 caps 兼容性
        if not src_pad.can_link(parser_sink):
            print(f"  [ERROR] Caps incompatible!")
            print(f"  Source caps: {caps.to_string()}")
            parser_caps = parser_sink.query_caps(None)
            print(f"  Parser caps: {parser_caps.to_string()}")
            return
        
        # 8. 链接 qtdemux -> parser
        link_result = src_pad.link(parser_sink)
        if link_result != Gst.PadLinkReturn.OK:
            print(f"  [ERROR] Link failed: {link_result}")
            return
        
        print(f"  [OK] qtdemux -> {parser_name}")
        
        # 9. 链接 parser -> decoder
        if not parser.link(decoder):
            print(f"  [ERROR] Failed to link {parser_name} -> decoder")
            return
        print(f"  [OK] {parser_name} -> decoder")
        
        # 10. 链接 decoder -> streammux
        sinkpad = streammux.request_pad_simple("sink_0")
        srcpad = decoder.get_static_pad("src")
        if srcpad.link(sinkpad) != Gst.PadLinkReturn.OK:
            print(f"  [ERROR] Failed to link decoder -> streammux")
            return
        print(f"  [OK] decoder -> streammux")
        
        # 11. 链接 streammux -> tee
        if not streammux.link(tee):
            print(f"  [ERROR] Failed to link streammux -> tee")
            return
        print(f"  [OK] streammux -> tee")
        
        # 12. 链接三个并行分支
        try:
            # 分支1
            tee.request_pad_simple("src_0").link(queue1.get_static_pad("sink"))
            queue1.link(pgie1)
            pgie1.get_static_pad("src").link(metamux.request_pad_simple("sink_0"))
            print(f"  [OK] Branch 1: tee -> queue1 -> pgie1 -> metamux")
            
            # 分支2
            tee.request_pad_simple("src_1").link(queue2.get_static_pad("sink"))
            queue2.link(pgie2)
            pgie2.get_static_pad("src").link(metamux.request_pad_simple("sink_1"))
            print(f"  [OK] Branch 2: tee -> queue2 -> pgie2 -> metamux")
            
            # 分支3
            tee.request_pad_simple("src_2").link(queue3.get_static_pad("sink"))
            queue3.link(pgie3)
            pgie3.get_static_pad("src").link(metamux.request_pad_simple("sink_2"))
            print(f"  [OK] Branch 3: tee -> queue3 -> pgie3 -> metamux")
            
            # 13. 链接输出
            metamux.link(nvosd)
            nvosd.link(nvvidconv)
            nvvidconv.link(capsfilter)
            capsfilter.link(encoder)
            encoder.link(h264parser_enc)
            h264parser_enc.link(qtmux)
            qtmux.link(sink)
            print(f"  [OK] Output chain: metamux -> osd -> encoder -> sink")
            
            print(f"\n  [SUCCESS] Pipeline fully linked with {parser_name}!")
            
        except Exception as e:
            print(f"  [ERROR] Exception during linking: {e}")
            import traceback
            traceback.print_exc()
    
    # 连接回调
    qtdemux.connect("pad-added", qtdemux_pad_added)
    print("  [OK] Dynamic linking callback registered\n")

    # ==================== 添加 Probe ====================
    osdsinkpad = nvosd.get_static_pad("sink")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # ==================== 运行 ====================
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    print("="*80)
    print("Starting PARALLEL processing...")
    print("="*80 + "\n")
    
    start_time = time.time()
    ret = pipeline.set_state(Gst.State.PLAYING)
    
    if ret == Gst.StateChangeReturn.FAILURE:
        print("ERROR: Unable to set pipeline to PLAYING")
        sys.exit(1)
    
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED]")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    pipeline.set_state(Gst.State.NULL)
    total_time = time.time() - start_time
    avg_fps = fps_calculator.get_average_fps()
    
    print("\n" + "="*80)
    print("PARALLEL Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Total frames: {fps_calculator.frame_count}")
    print(f"   Average FPS: {avg_fps:.2f}")
    if os.path.exists(OUTPUT_VIDEO_PATH):
        file_size = os.path.getsize(OUTPUT_VIDEO_PATH) / (1024*1024)
        print(f"   Output: {OUTPUT_VIDEO_PATH} ({file_size:.2f} MB)")
    print("="*80 + "\n")

if __name__ == '__main__':
    sys.exit(main(sys.argv))