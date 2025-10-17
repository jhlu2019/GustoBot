#!/bin/bash
/home/kdsoft/miniconda3/envs/vllm-0.9.0/bin/vllm serve "/data/models/Qwen3-30B-A3B" \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.45 \
  --port 8000 \
  --max-model-len 32768 \
  --served-model-name "Qwen3-30B-A3B" \
  --api-key vR4TUrqfZ6n6YTgKzTNnHCZMtUab6EuI3FORzTpfARyoezkQZpyHMxbe \
  --enable-reasoning \
  --reasoning-parser deepseek_r1 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
