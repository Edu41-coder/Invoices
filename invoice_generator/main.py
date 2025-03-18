#!/usr/bin/env python3
"""
Invoice Generator - Command Line Interface
Generate realistic invoice datasets for document understanding tasks
"""
import argparse
import random
import numpy as np
import os
import sys
from pathlib import Path

from invoice_generator.generator import InvoiceGenerator
from invoice_generator.config import OUTPUT_DIRS

def main():
    """Main entry point for invoice generator"""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate invoice dataset for document understanding"
    )
    parser.add_argument(
        "-n", "--num", 
        type=int, 
        default=10, 
        help="Number of invoices to generate"
    )
    parser.add_argument(
        "--non-invoices", 
        type=int, 
        default=20, 
        help="Number of non-invoice documents to generate"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="dataset", 
        help="Output directory"
    )
    parser.add_argument(
        "--only-invoices", 
        action="store_true", 
        help="Only generate invoices (no non-invoices)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--split",
        nargs=3,
        type=float,
        default=[0.7, 0.15, 0.15],
        help="Dataset split ratios (train, val, test)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if sum(args.split) != 1.0:
        print("Error: Dataset split ratios must sum to 1.0")
        return 1
        
    # Set random seed if provided
    if args.seed:
        print(f"Using random seed: {args.seed}")
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Create generator
        generator = InvoiceGenerator(output_base=args.output)
        
        # Generate invoice dataset
        generator.generate_dataset(count=args.num, split=tuple(args.split))
        
        # Generate non-invoice documents unless disabled
        if not args.only_invoices:
            generator.create_non_invoice_documents(count=args.non_invoices, split=tuple(args.split))
        
        # Print summary
        print(f"\nDataset generation complete. Files saved to {args.output}/")
        generator.print_dataset_summary()
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())