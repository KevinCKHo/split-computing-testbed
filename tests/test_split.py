"""Sanity checks that run without the network or a GPU: python -m pytest -q"""
import socket
import threading

import numpy as np
import pytest
import torch

from splitbench import protocol
from splitbench.model import SPLIT_POINTS, load_backbone, split_model


@pytest.fixture(scope="module")
def model():
    torch.manual_seed(0)
    return load_backbone("resnet50", pretrained=False)


@pytest.mark.parametrize("split", SPLIT_POINTS)
def test_edge_plus_server_equals_full(model, split):
    x = torch.randn(1, 3, 224, 224)
    edge, server = split_model(model, split)
    with torch.inference_mode():
        assert torch.allclose(server(edge(x)), model(x), atol=1e-4)


def test_activation_shapes(model):
    x = torch.randn(1, 3, 224, 224)
    expect = {"layer1": (256, 56, 56), "layer2": (512, 28, 28), "layer3": (1024, 14, 14), "layer4": (2048, 7, 7)}
    with torch.inference_mode():
        for sp, shape in expect.items():
            assert tuple(split_model(model, sp)[0](x).shape[1:]) == shape


def test_protocol_roundtrip():
    a, b = socket.socketpair()
    arr = np.random.rand(256, 56, 56).astype(np.float32)
    t = threading.Thread(target=protocol.send_frame, args=(a, 7, arr), kwargs={"meta": {"split": "layer1"}})
    t.start()
    header, got = protocol.recv_frame(b)
    t.join()
    assert header["req"] == 7 and header["split"] == "layer1"
    np.testing.assert_array_equal(got, arr)
