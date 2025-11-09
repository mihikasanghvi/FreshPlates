from dataclasses import dataclass, field
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, set_seed
import json
import torch
import os
import subprocess

from optimum.neuron import NeuronHfArgumentParser as HfArgumentParser
from optimum.neuron import NeuronSFTConfig, NeuronSFTTrainer, NeuronTrainingArguments
from torch_xla.core.xla_model import is_master_ordinal
from optimum.neuron.models.training import NeuronModelForCausalLM

def format_conversation(example):
    text = ""
    for msg in example['messages']:
        role = msg['role']
        content = msg['content']
        if role == "system":
            text += f"<|system|>\n{content}\n"
        elif role == "user":
            text += f"<|user|>\n{content}\n"
        elif role == "assistant":
            text += f"<|assistant|>\n{content}\n"
    return {"text": text}

print("Starting Meal Planner Training")

def training_function(script_args, training_args):
    print(f"Loading dataset from: {script_args.dataset_path}")
    with open(script_args.dataset_path, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} examples")
    
    dataset = Dataset.from_list(data)
    dataset = dataset.shuffle(seed=23)
    print("Formatting conversations...")
    dataset = dataset.map(format_conversation, remove_columns=dataset.column_names)
    print(f"Formatted dataset size: {len(dataset)}")
    
    train_size = int(0.9 * len(dataset))
    train_dataset = dataset.select(range(train_size))
    eval_dataset = dataset.select(range(train_size, len(dataset)))
    print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

    print(f"Loading tokenizer: {script_args.tokenizer_id}")
    tokenizer = AutoTokenizer.from_pretrained(script_args.tokenizer_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"Tokenizer loaded, vocab size: {tokenizer.vocab_size}")

    print(f"Loading model: {script_args.model_id}")
    trn_config = training_args.trn_config
    dtype = torch.bfloat16 if training_args.bf16 else torch.float32
    print(f"Using dtype: {dtype}")
    model = NeuronModelForCausalLM.from_pretrained(
        script_args.model_id,
        trn_config,
        torch_dtype=dtype,
        use_flash_attention_2=False,
    )
    print("Model loaded successfully")

    print(f"Setting up LoRA config (r={script_args.lora_r}, alpha={script_args.lora_alpha})")
    config = LoraConfig(
        r=script_args.lora_r,
        lora_alpha=script_args.lora_alpha,
        lora_dropout=script_args.lora_dropout,
        target_modules=["q_proj", "gate_proj", "v_proj", "o_proj", "k_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    print("Creating SFT config...")
    args = training_args.to_dict()

    sft_config = NeuronSFTConfig(
        max_seq_length=1024,
        packing=True,
        dataset_text_field="text",
        **args,
    )

    print(f"SFT config created with max_seq_length=1024")

    print("Initializing NeuronSFTTrainer...")
    trainer = NeuronSFTTrainer(
        args=sft_config,
        model=model,
        peft_config=config,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
    print("Trainer initialized successfully")

    print("Starting training...")
    trainer.train()
    print("Training completed successfully")
    del trainer

@dataclass
class ScriptArguments:
    model_id: str = field(
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        metadata={"help": "The model that you want to train from the Hugging Face hub."}
    )
    tokenizer_id: str = field(
        default="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        metadata={"help": "The tokenizer used to tokenize text for fine-tuning."}
    )
    dataset_path: str = field(
        default="../data_preparation/meal_planning_dataset_20k.json",
        metadata={"help": "Path to the meal planning dataset"}
    )
    lora_r: int = field(
        default=16,
        metadata={"help": "LoRA r value to be used during fine-tuning."}
    )
    lora_alpha: int = field(
        default=32,
        metadata={"help": "LoRA alpha value to be used during fine-tuning."}
    )
    lora_dropout: float = field(
        default=0.05,
        metadata={"help": "LoRA dropout value to be used during fine-tuning."}
    )

if __name__ == "__main__":
    print("Parsing arguments...")
    parser = HfArgumentParser([ScriptArguments, NeuronTrainingArguments])
    script_args, training_args = parser.parse_args_into_dataclasses()
    print(f"Arguments parsed. Seed: {training_args.seed}")
    
    set_seed(training_args.seed)
    print("Starting training function...")
    training_function(script_args, training_args)
    print("Training function completed")

    if is_master_ordinal():
        print("Master ordinal - consolidating model...")
        input_ckpt_dir = os.path.join(
            training_args.output_dir, f"checkpoint-{training_args.max_steps}"
        )
        output_ckpt_dir = os.path.join(training_args.output_dir, "merged_model")
        print(f"Input checkpoint: {input_ckpt_dir}")
        print(f"Output directory: {output_ckpt_dir}")
        env = os.environ.copy()
        env["NEURON_RT_VISIBLE_CORES"] = "0-1"
        subprocess.run([
            "python3",
            "consolidate_adapter_shards_and_merge_model.py",
            "-i", input_ckpt_dir,
            "-o", output_ckpt_dir,
        ], env=env)
        print("Model consolidation completed")
    print("Training Complete")


