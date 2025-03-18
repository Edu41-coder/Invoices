import os
import argparse
from pathlib import Path
from invoice_model import InvoiceModel

def main():
    parser = argparse.ArgumentParser(description="Process invoices with trained models")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory with documents to process")
    parser.add_argument("--model_dir", type=str, default="model_output", help="Directory with trained models")
    parser.add_argument("--output_csv", type=str, default="results.csv", help="Output CSV file")
    
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
            
            if result["is_invoice"]:
                print(f"✓ Invoice detected: {img_path.name}")
                print(f"  Invoice #: {result['fields'].get('invoice_number', 'N/A')}")
                print(f"  Total: {result['fields'].get('total_ttc', 'N/A')}")
            else:
                print(f"✗ Not an invoice: {img_path.name}")
                
        except Exception as e:
            print(f"Error processing {img_path.name}: {str(e)}")
    
    print(f"Processing complete! Results stored in database: {args.model_dir}/invoices.db")

if __name__ == "__main__":
    main()