#!/bin/bash
CUDA_VISIBLE_DEVICES=0,1,2,3 /home/kdsoft/miniconda3/envs/deepseekocr/bin/vllm serve /data/models/DeepSeek-OCR \
  --trust_remote_code \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.1 \
  --port 8008 \
  --max-model-len 16384\
  --served-model-name DeepSeek-OCR \
  --api-key vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe
