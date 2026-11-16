# Copyright (c) 2026 Paulo Henrik Carvalho Araújo
# NarraVox Studios - CineGen Setup Builder
# Licença Apache 2.0

import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def build_installer():
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)

    print("=========================================================================")
    print("🎬 CINEGEN :: COMPILANDO EXECUTÁVEL DO INSTALADOR (Setup_CineGen.exe)")
    print("=========================================================================")

    app_name = "Setup_CineGen"
    entry_point = "cinegen_installer.py"
    dist_dir = base_dir / "dist"
    work_dir = base_dir / "build_installer_temp"

    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    params = [
        str(entry_point),
        f"--name={app_name}",
        "--onefile",
        "--noconsole",
        "--clean",
        f"--workpath={work_dir}",
        f"--distpath={dist_dir}",
        # Exclusões para manter o executável leve (sem embutir ML bruto)
        "--exclude-module=torch",
        "--exclude-module=torchvision",
        "--exclude-module=torchaudio",
        "--exclude-module=diffusers",
        "--exclude-module=transformers",
        "--exclude-module=scipy",
        "--exclude-module=matplotlib",
    ]

    # Se webview estiver instalado no runner, inclui os coletores
    try:
        import webview
        params.extend([
            "--collect-all=webview",
            "--collect-all=clr_loader",
            "--collect-all=pythonnet"
        ])
    except ImportError:
        pass

    PyInstaller.__main__.run(params)

    exe_path = dist_dir / f"{app_name}.exe"
    if exe_path.exists():
        print("=========================================================================")
        print(f"✅ EXECUTÁVEL GERADO COM SUCESSO: {exe_path.name} ({exe_path.stat().st_size / (1024*1024):.1f} MB)")
        print("=========================================================================")
    else:
        print("❌ Falha na geração do executável.")
        sys.exit(1)

if __name__ == "__main__":
    build_installer()
