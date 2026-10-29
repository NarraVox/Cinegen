import time
import torch
import orbitquant
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer

model_path = r"C:\CineGen\models\videos\Kandinsky-6-Lite-OrbitQuant-W4A4\text_encoder"

print("Loading Qwen with device_map auto (max 4.6GiB GPU, rest CPU)...")
t0 = time.time()
max_memory = {0: "4.6GiB", "cpu": "12GiB"}

encoder = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path,
    dtype=torch.bfloat16,
    device_map="auto",
    max_memory=max_memory,
)
print(f"Loaded in {time.time() - t0:.2f}s")
print("Device map:", encoder.hf_device_map)
print("GPU allocated:", torch.cuda.memory_allocated() / 1024**3, "GiB")
