# Copyright 2023 Sony Semiconductor Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
import tempfile
import unittest

import numpy as np
import torch

from mct_quantizers import PytorchActivationQuantizationHolder
from mct_quantizers.pytorch.load_model import pytorch_load_quantized_model
from mct_quantizers.pytorch.quantize_wrapper import PytorchQuantizationWrapper
from mct_quantizers.pytorch.quantizer_utils import get_working_device
from mct_quantizers.pytorch.quantizers.activation_inferable_quantizers.activation_lut_pot_inferable_quantizer import \
    ActivationLutPOTInferableQuantizer
from mct_quantizers.pytorch.quantizers.activation_inferable_quantizers.activation_pot_inferable_quantizer import \
    ActivationPOTInferableQuantizer
from mct_quantizers.pytorch.quantizers.activation_inferable_quantizers.activation_symmetric_inferable_quantizer import \
    ActivationSymmetricInferableQuantizer
from mct_quantizers.pytorch.quantizers.activation_inferable_quantizers.activation_uniform_inferable_quantizer import \
    ActivationUniformInferableQuantizer
from mct_quantizers.pytorch.quantizers.weights_inferable_quantizers.weights_lut_pot_inferable_quantizer import \
    WeightsLUTPOTInferableQuantizer
from mct_quantizers.pytorch.quantizers.weights_inferable_quantizers.weights_lut_symmetric_inferable_quantizer import \
    WeightsLUTSymmetricInferableQuantizer
from mct_quantizers.pytorch.quantizers.weights_inferable_quantizers.weights_pot_inferable_quantizer import \
    WeightsPOTInferableQuantizer
from mct_quantizers.pytorch.quantizers.weights_inferable_quantizers.weights_symmetric_inferable_quantizer import \
    WeightsSymmetricInferableQuantizer
from mct_quantizers.pytorch.quantizers.weights_inferable_quantizers.weights_uniform_inferable_quantizer import \
    WeightsUniformInferableQuantizer


class TestPytorchLoadModel(unittest.TestCase):

    def setUp(self):
        self.device = get_working_device()

    def _one_layer_model_save_and_load(self, layer_with_quantizer):
        x = torch.from_numpy(np.random.rand(1, 3, 99, 99).astype(np.float32)).to(self.device)
        pred = layer_with_quantizer(x).detach().cpu().numpy()

        _, tmp_h5_file = tempfile.mkstemp('.h5')

        torch.save(layer_with_quantizer, tmp_h5_file)

        loaded_model = (pytorch_load_quantized_model(tmp_h5_file))
        os.remove(tmp_h5_file)

        loaded_pred = loaded_model(x).detach().cpu().numpy()
        self.assertTrue(np.all(loaded_pred == pred))

    def test_save_and_load_activation_pot(self):
        num_bits = 3
        thresholds = [4.]
        signed = True
        quantizer = ActivationPOTInferableQuantizer(num_bits=num_bits,
                                                    threshold=thresholds,
                                                    signed=signed)
        layer_with_quantizer = PytorchActivationQuantizationHolder(quantizer)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_activation_symmetric(self):
        num_bits = 3
        thresholds = [4.]
        signed = True
        quantizer = ActivationSymmetricInferableQuantizer(num_bits=num_bits,
                                                          threshold=thresholds,
                                                          signed=signed)
        layer_with_quantizer = PytorchActivationQuantizationHolder(quantizer)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_activation_uniform(self):
        num_bits = 3
        min_range = [1.]
        max_range = [4.]
        quantizer = ActivationUniformInferableQuantizer(num_bits=num_bits,
                                                        min_range=min_range,
                                                        max_range=max_range)
        layer_with_quantizer = PytorchActivationQuantizationHolder(quantizer)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_activation_lut_pot(self):
        lut_values = [-25, 25]
        thresholds = [4.]
        num_bits = 3
        signed = True
        lut_values_bitwidth = 8
        eps = 1e-8

        quantizer = ActivationLutPOTInferableQuantizer(num_bits=num_bits,
                                                       lut_values=lut_values,
                                                       signed=signed,
                                                       threshold=thresholds,
                                                       lut_values_bitwidth=
                                                       lut_values_bitwidth,
                                                       eps=eps)

        layer_with_quantizer = PytorchActivationQuantizationHolder(quantizer)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_weights_pot(self):
        thresholds = [4., 0.5, 2.]
        num_bits = 2
        quantizer = WeightsPOTInferableQuantizer(num_bits=num_bits,
                                                 per_channel=True,
                                                 threshold=thresholds,
                                                 channel_axis=3)
        layer_with_quantizer = PytorchQuantizationWrapper(torch.nn.Conv2d(3, 10, 3),
                                                          {'weight': quantizer}).to(self.device)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_weights_symmetric(self):
        thresholds = [3., 6., 2.]
        num_bits = 2
        quantizer = WeightsSymmetricInferableQuantizer(num_bits=num_bits,
                                                       per_channel=True,
                                                       threshold=thresholds,
                                                       channel_axis=3)
        layer_with_quantizer = PytorchQuantizationWrapper(torch.nn.Conv2d(3, 10, 3),
                                                          {'weight': quantizer}).to(self.device)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_weights_uniform(self):
        min_range = [3., 6., 2.]
        max_range = [13., 16., 12.]
        num_bits = 2
        quantizer = WeightsUniformInferableQuantizer(num_bits=num_bits,
                                                     per_channel=True,
                                                     min_range=min_range,
                                                     max_range=max_range,
                                                     channel_axis=3)
        layer_with_quantizer = PytorchQuantizationWrapper(torch.nn.Conv2d(3, 10, 3),
                                                          {'weight': quantizer}).to(self.device)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_weights_lut_symmetric(self):
        lut_values = [-25, 25]
        per_channel = True
        num_bits = 8
        threshold = [3., 8., 7.]
        channel_axis = 3
        lut_values_bitwidth = 8
        eps = 1e-8
        quantizer = WeightsLUTSymmetricInferableQuantizer(num_bits=num_bits,
                                                          lut_values=lut_values,
                                                          threshold=threshold,
                                                          per_channel=per_channel,
                                                          channel_axis=channel_axis,
                                                          lut_values_bitwidth=lut_values_bitwidth,
                                                          eps=eps,
                                                          input_rank=4)
        layer_with_quantizer = PytorchQuantizationWrapper(torch.nn.Conv2d(3, 10, 3),
                                                          {'weight': quantizer}).to(self.device)
        self._one_layer_model_save_and_load(layer_with_quantizer)

    def test_save_and_load_weights_lut_pot(self):
        lut_values = [-25, 25]
        per_channel = True
        num_bits = 8
        threshold = [1., 8., 4.]
        channel_axis = 3
        lut_values_bitwidth = 8
        eps = 1e-8
        quantizer = WeightsLUTPOTInferableQuantizer(num_bits=num_bits,
                                                    lut_values=lut_values,
                                                    threshold=threshold,
                                                    per_channel=per_channel,
                                                    channel_axis=channel_axis,
                                                    lut_values_bitwidth=lut_values_bitwidth,
                                                    eps=eps,
                                                    input_rank=4)
        layer_with_quantizer = PytorchQuantizationWrapper(torch.nn.Conv2d(3, 10, 3),
                                                          {'weight': quantizer}).to(self.device)
        self._one_layer_model_save_and_load(layer_with_quantizer)
