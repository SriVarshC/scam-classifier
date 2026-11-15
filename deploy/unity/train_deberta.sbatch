#!/usr/bin/env bash
# Fine-tune DeBERTa-v3-small on every split (A, B_*, R) on a Unity GPU - same model and settings as the
# Colab notebook (notebooks/deberta_colab.ipynb). Submit from the scam-classifier folder on Unity:
#   sbatch train_deberta.sbatch            (results -> results/metrics_deberta*.csv, summary_deberta.md)
# GPU: any card with compute capability >= 7.0 (V100, RTX 2080 Ti, A100, L4, L40S, ...); the M40/Titan X
# (sm_52) are too old for current PyTorch builds.
#SBATCH --job-name=scam-deberta
#SBATCH --partition=gpu
#SBATCH --qos=normal
#SBATCH --gpus=1
#SBATCH --constraint=sm_70|sm_75|sm_80|sm_86|sm_89|sm_90
#SBATCH --cpus-per-task=4
#SBATCH --mem=30G
#SBATCH --time=04:00:00
#SBATCH --output=results/%x-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
export HF_HOME="$PWD/.hf" HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false
echo "node=$(hostname) gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
cd src
../.venv/bin/python run_experiment.py --use-transformer "$@"
