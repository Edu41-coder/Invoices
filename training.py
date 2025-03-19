import os
import argparse
import cv2
import numpy as np
from pathlib import Path
from invoice_model import InvoiceModel
from datetime import datetime

def is_image_empty(image_path, threshold=0.99):
    """Détecte si une image est vide ou presque vide"""
    try:
        # Charger l'image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Impossible de charger {image_path}")
            return True
            
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculer le pourcentage de pixels blancs ou presque blancs
        white_pixels = np.sum(gray > 240)
        total_pixels = gray.size
        white_ratio = white_pixels / total_pixels
        
        return white_ratio > threshold
    except Exception as e:
        print(f"Erreur lors de l'analyse de {image_path}: {e}")
        return True

def clean_dataset(base_dir):
    """Nettoie le jeu de données en supprimant les images vides"""
    print(f"Nettoyage du répertoire: {base_dir}")
    dataset_dir = Path(base_dir)
    empty_count = 0
    
    # Parcourir tous les fichiers d'images
    for img_path in dataset_dir.glob('**/*.jpg'):
        if is_image_empty(img_path):
            print(f"Image vide détectée: {img_path}")
            os.remove(img_path)
            empty_count += 1
    
    if empty_count > 0:
        print(f"{empty_count} images vides supprimées")
    else:
        print("Aucune image vide détectée")
    
    return empty_count

def main():
    parser = argparse.ArgumentParser(description="Train invoice models")
    parser.add_argument("--train_dir", type=str, required=True, help="Directory with training data")
    parser.add_argument("--val_dir", type=str, required=True, help="Directory with validation data")
    parser.add_argument("--model_dir", type=str, default="model_output", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--negative_dir", type=str, help="Directory with non-invoice documents")
    parser.add_argument("--clean", action="store_true", help="Clean dataset before training")
    parser.add_argument("--train_ner", action="store_true", help="Train the NER model as well")
    
    args = parser.parse_args()
    
    # Nettoyer les données si demandé
    if args.clean:
        clean_dataset(args.train_dir)
        clean_dataset(args.val_dir)
    
    # Créer le répertoire de sortie si nécessaire
    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    
    # Créer un fichier de log pour l'entraînement
    log_file = Path(args.model_dir) / f"training_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, "w") as f:
        f.write(f"Training started at: {datetime.now()}\n")
        f.write(f"Parameters: {args}\n\n")
    
    # Create model with specified output directory
    model = InvoiceModel(model_dir=args.model_dir)
    
    # Choisir quel modèle entraîner
    if args.train_ner:
        print(f"Training NER model with {args.epochs} epochs...")
        model.train_ner_model(
            args.train_dir,
            args.val_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )
    else:
        # Train the classifier (default option)
        print(f"Training classifier with {args.epochs} epochs...")
        model.train_classifier(
            args.train_dir, 
            args.val_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            negative_dir=args.negative_dir or "dataset/training/non_invoices"
        )
    
    # Mise à jour du fichier de log
    with open(log_file, "a") as f:
        f.write(f"Training completed at: {datetime.now()}\n")
    
    print("Training complete!")

if __name__ == "__main__":
    main()