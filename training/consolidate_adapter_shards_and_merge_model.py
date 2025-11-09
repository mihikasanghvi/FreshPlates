from optimum.neuron.models.training import (
    consolidate_model_parallel_checkpoints_to_unified_checkpoint,
)
from transformers import AutoModelForCausalLM, AutoTokenizer
from argparse import ArgumentParser
from shutil import copyfile
import os
import peft

parser = ArgumentParser()
parser.add_argument(
    "-i",
    "--input_dir",
    help="Source checkpoint directory containing sharded adapter checkpoint files (e.g. checkpoint-1000)",
    required=True,
)
parser.add_argument(
    "-o",
    "--output_dir",
    help="Destination directory for final merged model (adapters merged into base model)",
    required=True,
)
args = parser.parse_args()

input_dir = args.input_dir
output_dir = args.output_dir
consolidated_ckpt_dir = os.path.join(input_dir, "consolidated")

# 1️⃣ Consolidate adapter shards (Trainium produces dp_rank shards)
print("Consolidating LoRA adapter shards...")
consolidate_model_parallel_checkpoints_to_unified_checkpoint(
    input_dir, consolidated_ckpt_dir
)

# 2️⃣ Copy adapter config into consolidated directory
adapter_config_src = os.path.join(input_dir, "adapter_default", "adapter_config.json")
adapter_config_dst = os.path.join(consolidated_ckpt_dir, "adapter_config.json")
copyfile(adapter_config_src, adapter_config_dst)

# 3️⃣ Load the PEFT adapter model (requires base_model_name from adapter_config.json)
print("Loading PEFT adapter model...")
peft_model = peft.AutoPeftModelForCausalLM.from_pretrained(consolidated_ckpt_dir)

# 4️⃣ Merge LoRA adapter weights into base model
print("Merging adapter into base model...")
merged_model = peft_model.merge_and_unload()

# 5️⃣ Save merged model + tokenizer
print(f"Saving merged model to {output_dir}")
merged_model.save_pretrained(output_dir)

# Tokenizer: try input_dir first, fallback to base model name
try:
    tokenizer = AutoTokenizer.from_pretrained(input_dir)
except Exception:
    from json import load
    with open(adapter_config_src) as f:
        cfg = load(f)
    base_model = cfg.get("base_model_name_or_path", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    tokenizer = AutoTokenizer.from_pretrained(base_model)

tokenizer.save_pretrained(output_dir)

# 6️⃣ Verify model loads correctly
print("\nMerge complete! Loading merged model to verify:")
model = AutoModelForCausalLM.from_pretrained(output_dir)
print(model.config)
