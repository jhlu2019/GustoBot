#!/bin/bash
export MODELSCOPE_CACHE=/data/models
export VLLM_USE_MODELSCOPE=true

/home/kdsoft/miniconda3/envs/vllm-0.10.1/bin/vllm serve /data/models/Skywork-R1V3-38B \
  --trust_remote_code \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.5 \
  --port 8002 \
  --max-model-len 16384\
  --served-model-name Skywork-R1V3-38B \
  --api-key vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe
