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
// NvDsPreProcessMeta

#include "bind_string_property_definitions.h"
#include "bindpreprocessmeta.hpp"
#include "nvdspreprocess_meta.h"
#include "nvds_roi_meta.h"

namespace py = pybind11;

namespace pydeepstream {

    void bindpreprocessmeta(py::module &m) {
        // Bind the NvDsPreProcessTensorMeta structure
        py::class_<NvDsPreProcessTensorMeta>(m, "NvDsPreProcessTensorMeta",
                                            pydsdoc::nvdspreprocessmetadoc::NvDsPreProcessTensorMetaDoc::descr)
            .def(py::init<>()) // Constructor
            .def_readwrite("raw_tensor_buffer", &NvDsPreProcessTensorMeta::raw_tensor_buffer)
            .def_readwrite("buffer_size", &NvDsPreProcessTensorMeta::buffer_size)
            .def_readwrite("tensor_shape", &NvDsPreProcessTensorMeta::tensor_shape)
            .def_readwrite("data_type", &NvDsPreProcessTensorMeta::data_type)
            .def_readwrite("tensor_name", &NvDsPreProcessTensorMeta::tensor_name)
            .def_readwrite("gpu_id", &NvDsPreProcessTensorMeta::gpu_id)
            .def_readwrite("private_data", &NvDsPreProcessTensorMeta::private_data)
            .def_readwrite("meta_id", &NvDsPreProcessTensorMeta::meta_id)
            .def_readwrite("maintain_aspect_ratio", &NvDsPreProcessTensorMeta::maintain_aspect_ratio)
            .def("cast",
                [](void *data) {
                    return (NvDsPreProcessTensorMeta *) data;
                },
                py::return_value_policy::reference,
                pydsdoc::nvdspreprocessmetadoc::NvDsPreProcessTensorMetaDoc::cast);

        // Bind the GstNvDsPreProcessBatchMeta structure
        py::class_<GstNvDsPreProcessBatchMeta>(m, "GstNvDsPreProcessBatchMeta",
                                              pydsdoc::nvdspreprocessmetadoc::GstNvDsPreProcessBatchMetaDoc::descr)
            .def(py::init<>()) // Constructor
            .def_readwrite("target_unique_ids", &GstNvDsPreProcessBatchMeta::target_unique_ids)
            .def_readwrite("tensor_meta", &GstNvDsPreProcessBatchMeta::tensor_meta)
            .def_readwrite("roi_vector", &GstNvDsPreProcessBatchMeta::roi_vector)
            .def_readwrite("private_data", &GstNvDsPreProcessBatchMeta::private_data)
            .def("cast",
                [](void *data) {
                    return (GstNvDsPreProcessBatchMeta *) data;
                },
                py::return_value_policy::reference,
                pydsdoc::nvdspreprocessmetadoc::GstNvDsPreProcessBatchMetaDoc::cast);
    }

}