import os
import argparse
from pathlib import Path
from invoice_model import InvoiceModel

def main():
    parser = argparse.ArgumentParser(description="Train invoice models")
    parser.add_argument("--train_dir", type=str, required=True, help="Directory with training data")
    parser.add_argument("--val_dir", type=str, required=True, help="Directory with validation data")
    parser.add_argument("--model_dir", type=str, default="model_output", help="Directory to save models")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for training")
    parser.add_argument("--learning_rate", type=float, default=5e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    # Create model with specified output directory
    model = InvoiceModel(model_dir=args.model_dir)
    
    # Train the classifier
    print(f"Training classifier with {args.epochs} epochs...")
    model.train_classifier(
        args.train_dir, 
        args.val_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    print("Training complete!")

if __name__ == "__main__":
    main()