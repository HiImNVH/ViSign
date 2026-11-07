"""Tao clip WebM VP8 tong hop 2 giay (khong co nguoi) cho smoke CI; khong commit media vao repo.

Chay trong image API (co PyAV): python make_clip.py <duong-dan-ra.webm>
"""

import sys

import av
import numpy as np

with av.open(sys.argv[1], "w") as container:
    stream = container.add_stream("libvpx", rate=15)
    stream.width, stream.height, stream.pix_fmt = 320, 240, "yuv420p"
    for index in range(30):
        pixels = np.full((240, 320, 3), (index * 8) % 255, dtype=np.uint8)
        for packet in stream.encode(av.VideoFrame.from_ndarray(pixels, format="rgb24")):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
