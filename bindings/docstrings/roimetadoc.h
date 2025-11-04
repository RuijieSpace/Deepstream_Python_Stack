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
    namespace NvDsRoiMetaDoc 
    {
        namespace NvDsDataTypeDoc {
            constexpr const char* descr = R"pyds(*Enumerator*. Specifies the type of meta data.)pyds";
            
            constexpr const char* NvDsDataType_FP32=R"pyds(FP32 data type.)pyds"; 
            constexpr const char* NvDsDataType_UINT8=R"pyds(UINT8 data type.)pyds";
            constexpr const char* NvDsDataType_INT8=R"pyds(INT8 data type.)pyds"; 
            constexpr const char* NvDsDataType_UINT32=R"pyds(UINT32 data type.)pyds";
            constexpr const char* NvDsDataType_INT32=R"pyds(INT32 data type.)pyds";
            constexpr const char* NvDsDataType_FP16=R"pyds(FP16 data type.)pyds";
        }

        namespace NvDsUnitTypeDoc {
            constexpr const char* descr = R"pyds(*Enumerator*. Specifies the type of meta data.)pyds";
            
            constexpr const char* NvDsUnitType_FullFrame=R"pyds(Full frames.)pyds"; 
            constexpr const char* NvDsUnitType_ROI=R"pyds(Region of Interests (ROIs).)pyds";
            constexpr const char* NvDsUnitType_Object=R"pyds(Object mode.)pyds"; 
        }

        namespace NvDsRoiMetaDoc {
            constexpr const char* descr = R"pyds(
                Holds Information about ROI Metadata.
                
                :ivar roi: :class:`NvOSD_RectParams`, ROI bounding box.
                :ivar converted_buffer: pointer to :class:`NvBufSurfaceParams`, scaled & converted buffer to processing width/height.
                :ivar frame_meta: pointer to :class:`NvDsFrameMeta`, deepstream frame meta.
                :ivar scale_ratio_x: *float*, ratio by which the frame/ROI crop was scaled in horizontal direction Required when scaling co-ordinates/sizes in metadata back to input resolution.
                :ivar scale_ratio_y: *float*, ratio by which the frame/ROI crop was scaled in vertical direction Required when scaling co-ordinates/sizes in metadata back to input resolution.
                :ivar offset_left: *float*, offsets in horizontal direction while scaling.
                :ivar offset_top: *float*, offsets in vertical direction while scaling.
                :ivar classifier_meta_list: A list of items of type :class:`NvDsClassifierMeta`.
                :ivar roi_user_meta_list: A list of items of type :class:`NvDsUserMeta`.
                :ivar object_meta: pointer to :class:`NvDsObjectMeta`, deepstream object meta.)pyds";
            constexpr const char* cast = R"pyds(Casts a pointer to :class:`NvDsRoiMeta`)pyds";
        }
    }  
}  
