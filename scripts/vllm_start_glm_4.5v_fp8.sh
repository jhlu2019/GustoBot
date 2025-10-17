#!/bin/bash
export MODELSCOPE_CACHE=/data/models
export VLLM_USE_MODELSCOPE=true

/home/kdsoft/miniconda3/envs/glm-4.5v/bin/vllm serve /data/models/GLM-4.5V-FP8 \
  --trust_remote_code \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.6 \
  --port 8003 \
  --max-model-len 16384\
  --served-model-name GLM-4.5V \
  --api-key vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe \
  --tool-call-parser glm45   \
  --enable-auto-tool-choice
