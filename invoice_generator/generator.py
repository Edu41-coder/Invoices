import os
import random
import shutil
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

from invoice_generator.data_provider import DataProvider, fake
from invoice_generator.image_effects import ImageEffects
from invoice_generator.pdf_utils import InvoicePDF, convert_pdf_to_image
from invoice_generator.document_types import (
    LetterGenerator, 
    MemoGenerator, 
    ReportGenerator, 
    FormGenerator
)
from invoice_generator.config import LAYOUTS, OUTPUT_DIRS, FONTS

class InvoiceGenerator:
    """Main class for generating invoice datasets"""
    
    def __init__(self, output_base="dataset"):
        # Initialize components
        self.data_provider = DataProvider()
        self.image_effects = ImageEffects()
        self.invoice_pdf = InvoicePDF(data_provider=self.data_provider)
        
        # Initialize document generators
        self.letter_generator = LetterGenerator(self.data_provider, self.image_effects)
        self.memo_generator = MemoGenerator(self.data_provider, self.image_effects)
        self.report_generator = ReportGenerator(self.data_provider, self.image_effects)
        self.form_generator = FormGenerator(self.data_provider, self.image_effects)
        
        # Set output directory
        self.output_base = output_base
        self.dirs = {
            key: os.path.join(self.output_base, value.split('/')[-1]) 
            for key, value in OUTPUT_DIRS.items()
        }
        
        # Create output directories
        for dir_name in self.dirs.values():
            os.makedirs(dir_name, exist_ok=True)
    
    def generate_dataset(self, count=1000, split=(0.7, 0.15, 0.15)):
        """Generate a complete dataset with the specified count and split ratio"""
        print(f"Generating {count} invoices...")
        
        train_count = int(count * split[0])
        val_count = int(count * split[1])
        test_count = count - train_count - val_count
        
        print(f"Training: {train_count}, Validation: {val_count}, Test: {test_count}")
        
        # Generate training data
        print("Generating training invoices...")
        self._generate_batch(train_count, self.dirs["training_invoices"], defect_prob=0.6, handwriting_prob=0.5)
        
        # Generate validation data
        print("Generating validation invoices...")
        self._generate_batch(val_count, self.dirs["validation_invoices"], defect_prob=0.6, handwriting_prob=0.5)
        
        # Generate test data
        print("Generating test invoices...")
        self._generate_batch(test_count, self.dirs["test_invoices"], defect_prob=0.6, handwriting_prob=0.5)
        
        # Generate a few original clean invoices for reference
        print("Generating clean samples...")
        self._generate_batch(10, self.dirs["original"], defect_prob=0, handwriting_prob=0)
        
        # Generate a few sample invoices for testing
        print("Generating sample invoices...")
        self._generate_batch(5, self.dirs["sample"], defect_prob=0.5, handwriting_prob=0.5)
    
    def _generate_batch(self, count, output_dir, defect_prob=0.5, handwriting_prob=0.3):
        """Generate a batch of invoices with the specified probabilities of defects and handwriting"""
        for i in range(count):
            # Pick company type
            company_type = random.choice(['diy', 'tech', 'retail', 'insurance', 'telecom', 'healthcare'])
            
            # Get appropriate companies and items for this type
            companies, items = self.data_provider.get_items_for_company_type(company_type)
            company_name = random.choice(companies)
            
            # Generate invoice data
            invoice_num = f"INV-{random.randint(10000, 99999)}"
            date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%d/%m/%Y")
            client_name = fake.name()
            client_address = fake.address().replace('\n', ', ')
            
            # Choose layout and format
            layout = random.choice(LAYOUTS)
            output_format = random.choice(["pdf", "jpg", "jpeg"])
            
            # Generate PDF invoice
            pdf_path = os.path.join(self.dirs["temp"], f"temp_{invoice_num}.pdf")
            
            # Transformer les chaînes en dictionnaires avec les propriétés attendues
            formatted_items = []
            for item in items:
                formatted_items.append({
                    "description": item,
                    "amount": random.randint(1, 10),
                    "unit_price": round(random.uniform(10, 500), 2)
                })

            self.invoice_pdf.generate_invoice_pdf(
                company_name, company_type, invoice_num, date,
                client_name, client_address, formatted_items, layout, pdf_path
            )
            
            # Convert to image if needed
            if output_format != "pdf":
                # Convert PDF to image
                img_path = os.path.join(output_dir, f"invoice_{i+1}.{output_format}")
                apply_defects = random.random() < defect_prob
                add_handwriting = random.random() < handwriting_prob
                
                convert_pdf_to_image(
                    pdf_path, 
                    img_path, 
                    self.image_effects if (apply_defects or add_handwriting) else None
                )
                
                # Remove the temporary PDF
                os.remove(pdf_path)
            else:
                # Just copy the PDF to the output directory
                dest_path = os.path.join(output_dir, f"invoice_{i+1}.pdf")
                shutil.copy(pdf_path, dest_path)
                os.remove(pdf_path)
    
    def create_non_invoice_documents(self, count=100, split=(0.7, 0.15, 0.15)):
        """Generate non-invoice documents distributed across training/validation/test"""
        print(f"Generating {count} non-invoice documents...")
        
        # Calculate counts based on split ratio
        train_count = int(count * split[0])
        val_count = int(count * split[1])
        test_count = count - train_count - val_count
        
        print(f"Training non-invoices: {train_count}, Validation: {val_count}, Test: {test_count}")
        
        # Types of non-invoice documents to generate
        doc_generators = {
            "letter": self.letter_generator,
            "memo": self.memo_generator,
            "report": self.report_generator,
            "form": self.form_generator
        }
        
        # Generate for training set
        self._create_non_invoice_batch(train_count, self.dirs["training_non_invoices"], doc_generators)
        
        # Generate for validation set
        self._create_non_invoice_batch(val_count, self.dirs["validation_non_invoices"], doc_generators)
        
        # Generate for test set
        self._create_non_invoice_batch(test_count, self.dirs["test_non_invoices"], doc_generators)

    def _create_non_invoice_batch(self, count, output_dir, doc_generators):
        """Generate a batch of non-invoice documents"""
        os.makedirs(output_dir, exist_ok=True)
        
        for i in range(count):
            doc_type, generator = random.choice(list(doc_generators.items()))
            output_path = os.path.join(output_dir, f"{doc_type}_{i+1}.jpg")
            generator.generate_document(output_path)
    
    def print_dataset_summary(self):
        """Print a summary of the generated dataset"""
        print("\nDataset Summary:")
        for dir_name, dir_path in self.dirs.items():
            if os.path.exists(dir_path):  # Only count directories that exist
                files = list(Path(dir_path).glob("*.jpg")) + list(Path(dir_path).glob("*.jpeg")) + list(Path(dir_path).glob("*.pdf"))
                print(f"  {dir_name}: {len(files)} files")