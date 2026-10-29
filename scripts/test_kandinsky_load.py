"""Test script to verify pipeline loading with local weights and cache."""
import json
from pathlib import Path
import torch

MODEL_DIR = Path(r"C:\CineGen\models\videos\Kandinsky-6-Lite-OrbitQuant-W4A4")
SOURCE_SNAPSHOT = Path.home() / ".cache" / "huggingface" / "hub" / "models--kandinskylab--Kandinsky-6.0-Lite-distill-5s-Diffusers" / "snapshots" / "efbaeb9961770cc82fece5b9cb2197049d8c983c"

def test():
    print("Testing pipeline loader...")
    from diffusers import Kandinsky6TI2VAPipeline, Kandinsky6Transformer3DModel
    from transformers import Qwen2_5_VLForConditionalGeneration
    import orbitquant

    print("Loading quantized DiT from:", MODEL_DIR)
    transformer = Kandinsky6Transformer3DModel.from_pretrained(
        str(MODEL_DIR), torch_dtype=torch.bfloat16
    )
    print("DiT loaded! Loading Qwen text encoder from:", MODEL_DIR / "text_encoder")
    encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR / "text_encoder"), dtype=torch.bfloat16
    )
    print("Qwen loaded! Loading Kandinsky6TI2VAPipeline from source snapshot:", SOURCE_SNAPSHOT)
    pipe = Kandinsky6TI2VAPipeline.from_pretrained(
        str(SOURCE_SNAPSHOT),
        transformer=transformer,
        text_encoder=encoder,
        torch_dtype=torch.bfloat16,
    )
    print("Pipeline initialized successfully!")

if __name__ == "__main__":
    test()
