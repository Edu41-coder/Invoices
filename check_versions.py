import sys
import torch
import transformers
import numpy as np
from PIL import Image
import pytesseract

def check_versions():
    print(f"Python version: {sys.version}")
    print("\nVersions des bibliothèques:")
    print(f"torch: {torch.__version__}")
    print(f"transformers: {transformers.__version__}")
    print(f"PIL/Pillow: {Image.__version__}")
    print(f"numpy: {np.__version__}")
    
    try:
        print(f"pytesseract: {pytesseract.__version__}")
    except:
        print("pytesseract: version inconnue")
    
    print("\nVérification de la compatibilité:")
    
    # Vérifier les versions compatibles pour LayoutLM
    transformers_ok = False
    try:
        from packaging import version
        transformers_ver = version.parse(transformers.__version__)
        # LayoutLM fonctionne mieux avec des versions spécifiques
        transformers_ok = version.parse("4.5.0") <= transformers_ver <= version.parse("4.26.0")
    except:
        pass
    
    print(f"- transformers compatible avec LayoutLM: {'OUI' if transformers_ok else 'NON, version 4.5.0-4.26.0 recommandée'}")

    # Vérifier CUDA
    print(f"\nSupport GPU:")
    print(f"- CUDA disponible: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"- Nombre de GPUs: {torch.cuda.device_count()}")
        print(f"- Nom du GPU: {torch.cuda.get_device_name(0)}")
        print(f"- Version CUDA: {torch.version.cuda}")
    else:
        print("- Entraînement sur CPU (plus lent)")

if __name__ == "__main__":
    check_versions()