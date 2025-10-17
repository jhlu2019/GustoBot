#!/bin/bash
/home/kdsoft/miniconda3/envs/PaddleOCR-VL/bin/paddleocr genai_server \
 --host 0.0.0.0 \
 --port 8006 \
 --model_name PaddleOCR-VL-0.9B \
 --model_dir /data/models/PaddleOCR-VL/PaddleOCR-VL-0.9B \
 --backend vllm \
 --backend_config /data/models/PaddleOCR-VL/vllm_config.yaml
