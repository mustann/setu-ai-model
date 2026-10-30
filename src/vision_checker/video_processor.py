"""
Video Frame Extraction & Deduplication Module for Civic Media (Model 1).
Samples key frames across video duration using OpenCV,
removes near-identical consecutive frames, and returns representative frames.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image


class VideoProcessor:
    def __init__(self, max_frames: int = 8, diff_threshold: float = 15.0):
        self.max_frames = max_frames
        self.diff_threshold = diff_threshold

    def _is_different(self, frame_a: np.ndarray, frame_b: np.ndarray) -> bool:
        """
        Calculates mean absolute difference between downsampled grayscale versions of two frames.
        """
        small_a = cv2.resize(cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY), (64, 64))
        small_b = cv2.resize(cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY), (64, 64))
        diff = float(np.mean(np.abs(small_a.astype(np.float32) - small_b.astype(np.float32))))
        return diff > self.diff_threshold

    def extract_keyframes_from_path(self, video_path: str | Path) -> Tuple[List[Image.Image], int]:
        """
        Returns (useful_keyframes, total_frames_sampled)
        """
        video_path = str(video_path)
        if not os.path.exists(video_path):
            return [], 0

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return [], 0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return [], 0

        # Sample across video duration
        num_samples = min(self.max_frames, max(1, total_frames))
        step = max(1, total_frames // (num_samples + 1))
        indices = [step * (i + 1) for i in range(num_samples)]

        raw_frames: List[np.ndarray] = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                raw_frames.append(frame)

        cap.release()
        frames_sampled = len(raw_frames)

        if not raw_frames:
            return [], 0

        # Deduplicate consecutive frames
        useful_cv_frames: List[np.ndarray] = [raw_frames[0]]
        for curr in raw_frames[1:]:
            if self._is_different(useful_cv_frames[-1], curr):
                useful_cv_frames.append(curr)

        # Convert to PIL RGB Images
        keyframes: List[Image.Image] = [
            Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            for f in useful_cv_frames
        ]

        return keyframes, frames_sampled

    def extract_keyframes_from_bytes(self, video_bytes: bytes, suffix: str = ".mp4") -> Tuple[List[Image.Image], int]:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            return self.extract_keyframes_from_path(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
