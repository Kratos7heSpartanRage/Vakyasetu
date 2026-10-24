#!/usr/bin/env bash
# Reproduces the run that produced the final adapter ("run 2"): LoRA fine-tuning of IndicTrans2
# (Sanskrit -> English) on the cleaned Samayik data. About 2.5 hours on an RTX 2050 (4 GB).
# Results will be close to the reported ones but not bit-for-bit identical (GPU nondeterminism).
#
# Prerequisites (see README):
#   1. environment installed, Hugging Face login done, the IndicTransToolkit patch applied (training only)
#   2. python ml/scripts/inspect_samayik.py --write
#   3. python ml/scripts/prepare_lora_data.py --out-dir data/lora_full --dev-size 200
#   4. ml/scripts/train_lora_vs.py present (IndicTrans2's train_lora.py with one edit)
#
# Run in the background so closing the terminal does not stop it:
#   nohup bash ml/scripts/train_run2.sh > ml/outputs/run2_full.log 2>&1 &
# Watch progress:
#   tr '\r' '\n' < ml/outputs/run2_full.log | tail -3
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
TRAIN_SCRIPT="${TRAIN_SCRIPT:-$REPO/ml/scripts/train_lora_vs.py}"
DATA_DIR="${DATA_DIR:-$REPO/data/lora_full}"
OUT_DIR="${OUT_DIR:-$REPO/ml/checkpoints/run2_full}"

export CUDA_VISIBLE_DEVICES=0
cd "$(dirname "$TRAIN_SCRIPT")"   # run from the script's own folder, as it was when the results were produced

python3 -u "$TRAIN_SCRIPT" \
  --data_dir "$DATA_DIR" \
  --model ai4bharat/indictrans2-indic-en-dist-200M \
  --output_dir "$OUT_DIR" \
  --src_lang_list san_Deva --tgt_lang_list eng_Latn \
  --save_steps 500 --eval_steps 500 \
  --max_steps 4000 --batch_size 4 --grad_accum_steps 8 \
  --warmup_steps 200 --max_grad_norm 1.0 --learning_rate 2e-4 \
  --adam_beta1 0.9 --adam_beta2 0.98 --optimizer adamw_torch \
  --lr_scheduler linear --num_workers 2 \
  --metric_for_best_model eval_BLEU --greater_is_better --patience 3 \
  --weight_decay 0.01 --lora_target_modules "q_proj,k_proj" \
  --lora_dropout 0.1 --lora_r 16 --lora_alpha 32 --report_to none