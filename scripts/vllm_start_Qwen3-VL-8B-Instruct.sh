#!/bin/bash
export MODELSCOPE_CACHE=/data/models
export VLLM_USE_MODELSCOPE=true

/home/kdsoft/miniconda3/envs/qwen3-vl/bin/vllm serve /data/models/Qwen3-VL-8B-Instruct \
  --trust_remote_code \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.3 \
  --port 8003 \
  --max-model-len 16384\
  --served-model-name Qwen3-VL-8B-Instruct \
  --api-key vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe
