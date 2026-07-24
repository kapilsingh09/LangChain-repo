import os
import glob
import json

notebooks = glob.glob('*.ipynb')

replacements = {
    'google_genai:gemini-1.5-flash': 'gemini-1.5-flash',
    'gemini-3.5-flash': 'gemini-1.5-flash'
}

for nb_path in notebooks:
    with open(nb_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original_content = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original_content:
        with open(nb_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed models in {nb_path}")

print("Model strings fixed.")
