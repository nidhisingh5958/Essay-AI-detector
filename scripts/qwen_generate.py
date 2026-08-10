"""
Qwen2.5-1.5B-Instruct generation wrapper for EXP-DATA-001.

Per DEC-010/DEC-004, this model is used strictly as instructed -- it
generates text, nothing more. It never judges, labels, or scores its own
output or anyone else's; ground truth for every sample comes from the
known generation process (full generation vs. surgical splice vs.
diff-based polish), implemented in run_exp_data_001.py, never from asking
this model to assess anything.

Not unit-tested directly (would require loading a multi-GB model in the
test suite); the length-budgeting and truncation logic it depends on
lives in generation_utils.py and *is* tested there. The pilot run itself
is this module's real-world validation.
"""

import time
from dataclasses import dataclass
from functools import lru_cache

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


@lru_cache(maxsize=1)
def _load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype="auto")
    model.eval()
    return tokenizer, model


def model_revision() -> str:
    """Best-effort model identifier for reproducibility metadata."""
    _, model = _load_model()
    return getattr(model.config, "_commit_hash", None) or MODEL_NAME


@dataclass(frozen=True)
class GenerationResult:
    text: str
    generation_config: dict
    duration_seconds: float


def generate(instruction: str, max_new_tokens: int, temperature: float, top_p: float, seed: int) -> GenerationResult:
    tokenizer, model = _load_model()
    torch.manual_seed(seed)

    messages = [{"role": "user", "content": instruction}]
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt_text, return_tensors="pt")

    t0 = time.time()
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            pad_token_id=tokenizer.eos_token_id,
        )
    duration = time.time() - t0

    reply = tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    return GenerationResult(
        text=reply.strip(),
        generation_config={
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
            "max_new_tokens": max_new_tokens,
        },
        duration_seconds=duration,
    )
