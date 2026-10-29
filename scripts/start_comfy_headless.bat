@echo off
setlocal
set TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1
set TORCH_CUDNN_V8_API_ENABLED=1
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
cd /d "C:\CineGen\comfyui"
echo Iniciando ComfyUI com TF32 + INT8 Tensor Cores + VAE Tiled 256 otimizado...
"C:\CineGen\comfyui\.venv\Scripts\python.exe" main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --lowvram --enable-dynamic-vram --cuda-malloc
endlocal
