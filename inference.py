import os
import argparse
from pathlib import Path
from invoice_model import InvoiceModel

def main():
    parser = argparse.ArgumentParser(description="Process invoices with trained models")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory with documents to process")
    parser.add_argument("--model_dir", type=str, default="model_output", help="Directory with trained models")
    parser.add_argument("--output_csv", type=str, default="results.csv", help="Output CSV file")
    parser.add_argument("--verbose", action="store_true", help="Show detailed confidence scores")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    model = InvoiceModel(model_dir=args.model_dir)
    
    results = []
    
    # Process all images in input directory
    image_files = list(input_dir.glob("**/*.jpg")) + list(input_dir.glob("**/*.jpeg")) 
    image_files += list(input_dir.glob("**/*.pdf"))
    
    print(f"Found {len(image_files)} files to process")
    
    for i, img_path in enumerate(image_files):
        print(f"Processing {i+1}/{len(image_files)}: {img_path.name}")
        
        try:
            result = model.process_document(str(img_path))
            
            # Ajouter aux résultats pour CSV
            if result["is_invoice"]:
                row = {
                    "file_name": img_path.name, 
                    "is_invoice": "Yes",
                    **{k: v for k, v in result["fields"].items() if k != "confidence_scores"}
                }
            else:
                row = {"file_name": img_path.name, "is_invoice": "No"}
            results.append(row)
            
            if result["is_invoice"]:
                print(f"✓ Invoice detected: {img_path.name}")
                
                # Afficher les détails avec indicateurs de confiance
                for field, value in result["fields"].items():
                    if field == "confidence_scores":
                        continue
                    
                    # Vérifier si le champ est marqué comme incertain
                    uncertain = "[?]" in str(value) if isinstance(value, str) else False
                    
                    # Afficher avec un symbole pour les champs incertains
                    print(f"  {field}: {value} {'⚠️' if uncertain else ''}")
                
                # Afficher les scores détaillés si demandé
                if args.verbose and "confidence_scores" in result["fields"]:
                    print("  --- Scores de confiance ---")
                    for field, score in result["fields"]["confidence_scores"].items():
                        threshold = model.CONFIDENCE_THRESHOLDS.get(field, 0.7)
                        status = "✓" if score >= threshold else "❌"
                        print(f"    {field}: {score:.2f}/1.00 {status}")
            else:
                print(f"✗ Not an invoice: {img_path.name}")
                
        except Exception as e:
            print(f"Error processing {img_path.name}: {str(e)}")
            results.append({"file_name": img_path.name, "is_invoice": "Error", "error": str(e)})
    
    # Exporter vers CSV si demandé
    if results and args.output_csv:
        import csv
        try:
            with open(args.output_csv, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
            print(f"Results exported to {args.output_csv}")
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
    
    print(f"Processing complete! Results stored in database.")

if __name__ == "__main__":
    main()