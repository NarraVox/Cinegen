with open(r'C:\CineGen\comfyui\comfy\sd.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

patched = False
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'elif te_model == TEModel.QWEN3_4B:' in line:
        next_line = lines[i+1] if i+1 < len(lines) else ''
        if 'if clip_type == CLIPType.FLUX3:' not in next_line:
            indent = ' ' * (len(line) - len(line.lstrip()) + 4)
            patch = [
                f'{indent}if clip_type == CLIPType.FLUX3:\n',
                f'{indent}    clip_data[0] = comfy.utils.state_dict_prefix_replace(clip_data[0], {{"model.language_model.": "model.", "model.visual.": "visual.", "lm_head.": "model.lm_head."}})\n',
                f'{indent}    clip_target.clip = comfy.text_encoders.flux.flux3_te(**llama_detect(clip_data))\n',
                f'{indent}    clip_target.tokenizer = comfy.text_encoders.flux.Flux3Tokenizer\n',
                f'{indent}el' + lines[i+1].lstrip()
            ]
            new_lines.pop() # remove the te_model line temporarily
            new_lines.append(line)
            new_lines.extend(patch)
            # Skip the next line as it was converted to elif
            lines[i+1] = ''
            patched = True

if patched:
    with open(r'C:\CineGen\comfyui\comfy\sd.py', 'w', encoding='utf-8') as f:
        f.writelines([l for l in new_lines if l])
    print('[PATCH SUCCESS] sd.py patched for FLUX3 Qwen3-4B CLIP!')
else:
    print('[PATCH SKIP] Already patched or pattern not found')
