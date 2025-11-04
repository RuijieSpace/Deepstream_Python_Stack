/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

namespace pydsdoc 
{
    namespace nvdspreprocessmetadoc 
    {
        namespace NvDsPreProcessTensorMetaDoc {
            constexpr const char* descr = R"pyds(
                Tensor meta containing prepared tensor and related info inside preprocess user meta which is attached at batch level.

                :ivar raw_tensor_buffer: *capsule*, raw tensor buffer preprocessed for infer.
                :ivar max_elements_in_pool: *int*, size of raw tensor buffer.
                :ivar tensor_shape: *list of int*, raw tensor buffer shape.
                :ivar data_type: :class:`NvDsDataType`, model datatype for which tensor prepared.
                :ivar tensor_name: *string*, to be same as model input layer name.
                :ivar gpu_id: *int*, gpu-id on which tensor prepared.
                :ivar private_data: *capsule*, pointer to buffer from tensor pool.
                :ivar meta_id: *int*, meta id for differentiating between multiple tensor meta from same gst buffer,for the case when sum of roi's exceeds the batch size.
                :ivar maintain_aspect_ratio: *bool*, parameter to inform whether aspect ratio is maintained in the preprocess tensor.)pyds";
            constexpr const char* cast = R"pyds(Cast given object/data to :class:`NvDsPreProcessTensorMeta`, call pyds.NvDsPreProcessTensorMeta.cast(data))pyds";
        }

        namespace GstNvDsPreProcessBatchMetaDoc {
            constexpr const char* descr = R"pyds(Batch metadata structure for preprocessing operations.

                :ivar target_unique_ids: *list of int*, target unique ids for which meta is prepared.
                :ivar tensor_meta: :class:`NvDsPreProcessTensorMeta`, size of raw tensor buffer.
                :ivar roi_vector: *list of :class:`NvDsRoiMeta`*, list of roi vectors per batch.
                :ivar private_data: *capsule*, pointer to buffer from scaling pool.)pyds";
            constexpr const char* cast = R"pyds(Cast given object/data to :class:`GstNvDsPreProcessBatchMeta`, call pyds.GstNvDsPreProcessBatchMeta.cast(data))pyds";
        }
    }  
}

