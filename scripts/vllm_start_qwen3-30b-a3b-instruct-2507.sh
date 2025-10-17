#!/bin/bash
# 使用 /data/soft/models/Qwen3-30B-A3B-Instruct-2507 模型
# 使用 AWQ 量化，张量并行大小为 2
# GPU 内存利用率设定为 95%
# 服务运行在端口 8000
# 最大模型输入长度为 262144
# 服务的模型名称为 "Qwen/Qwen3-30B-A3B-Instruct-2507"
# API 密钥用于访问控制
# 启用推理功能，使服务可以进行更复杂的逻辑处理。

/home/kdsoft/miniconda3/envs/vllm-0.10.1/bin/vllm serve "/data/models/Qwen3-30B-A3B-Instruct-2507" \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.5 \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 16384 \
  --served-model-name "Qwen3-30B-A3B-Instruct-2507-FP16" \
  --api-key mrZqkvMiT4QjKa3H \
  --enable-expert-parallel

