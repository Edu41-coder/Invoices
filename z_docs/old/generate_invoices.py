from faker import Faker
from fpdf import FPDF, XPos, YPos
from fpdf.fonts import FontFace
import random
from datetime import datetime, timedelta
import os
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter, ImageOps
from pdf2image import convert_from_path
import numpy as np
import cv2
from pathlib import Path
import shutil

# Initialize Faker in French
fake = Faker(['fr_FR'])

class InvoiceGenerator:
    def __init__(self):
        # Base company lists from existing code
        self.diy_companies = [
            "LEROY MERLIN", "CASTORAMA", "BRICORAMA", "BRICO DÉPÔT",
            "BRICOMARCHÉ", "MR BRICOLAGE", "WELDOM", "BRICOMAN"
        ]
        
        self.tech_companies = [
            "Tech Solutions SARL", "InfoSys France", "Digital Services SA",
            "Consulting Pro EURL", "Web Expert SAS", "Data Analytics SARL",
            "Cloud Systems SAS", "Smart IT Services"
        ]
        
        self.retail_companies = [
            "CARREFOUR", "AUCHAN", "E.LECLERC", "INTERMARCHÉ",
            "SUPER U", "LIDL FRANCE", "CASINO", "MONOPRIX"
        ]
        
        # Add new sectors: Insurance, Telecom, and Healthcare
        self.insurance_companies = [
            "AXA France", "MAIF Assurances", "MATMUT", "Groupama",
            "Allianz France", "MMA Assurances", "Generali France", "AG2R La Mondiale"
        ]
        
        self.telecom_companies = [
            "ORANGE", "SFR", "BOUYGUES TELECOM", "FREE MOBILE",
            "SOSH", "RED by SFR", "B&YOU", "NRJ Mobile"
        ]
        
        self.healthcare_companies = [
            "Laboratoire Médical Central", "Centre Médical St-Jacques", "Pharmacie de la Gare", 
            "Clinique Médicale Express", "Analyse Biomédicale SARL", "Institut Paramédical",
            "Pharmacie du Boulevard", "Centre Optique Vision Plus"
        ]
        
        # All companies
        self.company_names = (self.diy_companies + self.tech_companies + 
                              self.retail_companies + self.insurance_companies + 
                              self.telecom_companies + self.healthcare_companies)
        
        # Expanded company styles
        self.company_styles = {
            # DIY
            "LEROY MERLIN": {"color": (67, 176, 42), "header": "BRICOLAGE - CONSTRUCTION - DÉCORATION - JARDINAGE"},
            "CASTORAMA": {"color": (0, 84, 166), "header": "BRICOLAGE - CONSTRUCTION - DÉCORATION - JARDINAGE"},
            
            # Tech
            "Tech Solutions SARL": {"color": (41, 128, 185), "header": "DÉVELOPPEMENT - CONSEIL - FORMATION - SUPPORT"},
            "InfoSys France": {"color": (52, 152, 219), "header": "SOLUTIONS - SERVICES - INNOVATION - TECHNOLOGIE"},
            
            # Distribution
            "CARREFOUR": {"color": (0, 0, 255), "header": "ALIMENTATION - MAISON - MODE - LOISIRS"},
            "AUCHAN": {"color": (227, 30, 45), "header": "HYPERMARCHÉ - SUPERMARCHÉ - DRIVE - PROXIMITÉ"},
            
            # Insurance
            "AXA France": {"color": (0, 71, 133), "header": "ASSURANCE - PRÉVENTION - ÉPARGNE - SANTÉ"},
            "MAIF Assurances": {"color": (232, 38, 46), "header": "ASSURANCE - BANQUE - PRÉVENTION - SERVICES"},
            
            # Telecom
            "ORANGE": {"color": (255, 90, 0), "header": "MOBILE - INTERNET - TV - TÉLÉPHONE"},
            "SFR": {"color": (226, 0, 60), "header": "TÉLÉPHONIE - INTERNET - FIBRE - 5G"},
            
            # Healthcare
            "Laboratoire Médical Central": {"color": (0, 153, 153), "header": "ANALYSES - PRÉLÈVEMENTS - RÉSULTATS - CONSULTATIONS"},
            "Pharmacie du Boulevard": {"color": (32, 147, 57), "header": "MÉDICAMENTS - PARAPHARMACIE - SANTÉ - BIEN-ÊTRE"},
        }
        
        # Items by sector (existing + new)
        self.diy_items = [
            "SOL ET CARRELAGE MURAL", "PEINTURE MURALE", "OUTILLAGE",
            "PLOMBERIE", "ÉLECTRICITÉ", "QUINCAILLERIE", "MENUISERIE"
        ]
        
        self.tech_items = [
            "Développement web", "Maintenance", "Formation",
            "Consultation", "Support technique", "Hébergement",
            "Design UX/UI", "SEO", "Développement mobile"
        ]
        
        self.retail_items = [
            "PRODUITS FRAIS", "ÉPICERIE", "BOISSONS",
            "HYGIÈNE", "ENTRETIEN", "TEXTILE",
            "MULTIMÉDIA", "PAPETERIE", "ACCESSOIRES"
        ]
        
        # New items for new sectors
        self.insurance_items = [
            "Assurance habitation", "Assurance auto", "Assurance santé",
            "Garantie accidents", "Prévoyance", "Protection juridique",
            "Assurance vie", "Responsabilité civile"
        ]
        
        self.telecom_items = [
            "Forfait mobile", "Box internet", "Options TV",
            "Téléphonie fixe", "Accessoires", "Extensions garantie",
            "Services cloud", "Installation fibre"
        ]
        
        self.healthcare_items = [
            "Consultation médicale", "Analyses sanguines", "Radiologie",
            "Médicaments prescrits", "Matériel médical", "Soins dentaires",
            "Optique", "Kinésithérapie"
        ]
        
        # Expanded fonts and layouts
        self.fonts = ["Helvetica", "Times", "Courier"]
        self.layouts = ["standard", "modern", "compact", "detailed", "minimal"]
        
        # Defect assets - will need to prepare these
        self.defect_assets = {
            "coffee_stains": self._load_defect_images("assets/coffee_stains"),
            "stamps": self._load_defect_images("assets/stamps"),
            "folds": self._load_defect_images("assets/folds")
        }
        
        # Handwriting assets - will need to prepare these
        self.handwriting_assets = self._load_defect_images("assets/handwriting")
        
        # Create output directories
        self.output_base = "dataset"
        self.dirs = {
            "original": os.path.join(self.output_base, "original"),
            "training": os.path.join(self.output_base, "training"),
            "validation": os.path.join(self.output_base, "validation"),
            "test": os.path.join(self.output_base, "test"),
            "sample": os.path.join(self.output_base, "sample")
        }
        
        for dir_name in self.dirs.values():
            os.makedirs(dir_name, exist_ok=True)
    
    def _load_defect_images(self, directory):
        """Load defect image assets from directory if it exists"""
        images = []
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        img_path = os.path.join(directory, filename)
                        img = Image.open(img_path).convert("RGBA")
                        images.append(img)
                    except:
                        print(f"Error loading image: {filename}")
        else:
            # Create directory for future assets
            os.makedirs(directory, exist_ok=True)
            
        # Return placeholder if no images found
        if not images:
            # Create a simple placeholder image
            img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((50, 50, 150, 150), fill=(200, 100, 0, 100))
            images.append(img)
            
        return images
    
    def generate_dataset(self, count=1000, split=(0.7, 0.15, 0.15)):
        """Generate a complete dataset with the specified count and split ratio"""
        print(f"Generating {count} invoices...")
        
        train_count = int(count * split[0])
        val_count = int(count * split[1])
        test_count = count - train_count - val_count
        
        print(f"Training: {train_count}, Validation: {val_count}, Test: {test_count}")
        
        # Generate training data
        print("Generating training data...")
        self._generate_batch(train_count, self.dirs["training"], defect_prob=0.6, handwriting_prob=0.5)
        
        # Generate validation data
        print("Generating validation data...")
        self._generate_batch(val_count, self.dirs["validation"], defect_prob=0.6, handwriting_prob=0.5)
        
        # Generate test data
        print("Generating test data...")
        self._generate_batch(test_count, self.dirs["test"], defect_prob=0.6, handwriting_prob=0.5)
        
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
            
            # Generate invoice based on company type
            if company_type == 'diy':
                company_name = random.choice(self.diy_companies)
                items = self.diy_items
            elif company_type == 'tech':
                company_name = random.choice(self.tech_companies)
                items = self.tech_items
            elif company_type == 'retail':
                company_name = random.choice(self.retail_companies)
                items = self.retail_items
            elif company_type == 'insurance':
                company_name = random.choice(self.insurance_companies)
                items = self.insurance_items
            elif company_type == 'telecom':
                company_name = random.choice(self.telecom_companies)
                items = self.telecom_items
            else:  # healthcare
                company_name = random.choice(self.healthcare_companies)
                items = self.healthcare_items
            
            # Generate invoice data
            invoice_num = f"INV-{random.randint(10000, 99999)}"
            date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%d/%m/%Y")
            client_name = fake.name()
            client_address = fake.address().replace('\n', ', ')
            
            # Choose layout and format
            layout = random.choice(self.layouts)
            output_format = random.choice(["pdf", "jpg", "jpeg"])
            
            # Generate PDF invoice
            pdf_path = self._generate_invoice_pdf(
                company_name, company_type, invoice_num, date,
                client_name, client_address, items, layout
            )
            
            # Convert to image if needed
            if output_format != "pdf":
                # Convert PDF to image
                img_path = os.path.join(output_dir, f"invoice_{i+1}.{output_format}")
                self._convert_and_enhance(pdf_path, img_path, 
                                         apply_defects=random.random() < defect_prob,
                                         add_handwriting=random.random() < handwriting_prob)
                # Remove the temporary PDF
                os.remove(pdf_path)
            else:
                # Just copy the PDF to the output directory
                dest_path = os.path.join(output_dir, f"invoice_{i+1}.pdf")
                shutil.copy(pdf_path, dest_path)
                os.remove(pdf_path)
    def _generate_invoice_pdf(self, company_name, company_type, invoice_num, date,
                        client_name, client_address, item_options, layout):        
        
        """Generate a PDF invoice with the given parameters"""
        # Create a temporary file path
        temp_dir = os.path.join(self.output_base, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"temp_{invoice_num}.pdf")

        # Initialize PDF with UTF-8 support
        pdf = FPDF()
        pdf.core_fonts_encoding = "utf-8"
        pdf.add_page()

        # Set font - using standard fonts
        font = random.choice(self.fonts)
        pdf.set_font(font, 'B', 16)

        # Company style
        company_style = self.company_styles.get(company_name, {"color": (0, 0, 0), "header": ""})
        color = company_style["color"]
        header = company_style["header"]

        # Set company color
        pdf.set_text_color(color[0], color[1], color[2])

        # Company header
        pdf.cell(0, 10, company_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font(font, '', 8)
        pdf.cell(0, 5, header, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        # Reset text color to black
        pdf.set_text_color(0, 0, 0)

        # Invoice details
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 10, 'FACTURE', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font(font, '', 10)
        pdf.cell(40, 7, f'N° Facture: {invoice_num}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(40, 7, f'Date: {date}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Client information
        pdf.ln(5)
        pdf.set_font(font, 'B', 12)
        pdf.cell(0, 8, 'Client:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font, '', 10)
        pdf.cell(0, 7, client_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(0, 7, client_address)

        # Items
        pdf.ln(10)
        pdf.set_font(font, 'B', 11)

        # Table header
        if layout == "standard" or layout == "detailed":
            pdf.cell(80, 7, 'Description', 1)
            pdf.cell(80, 7, 'Description', 1)
            pdf.cell(80, 7, 'Description', 1)
            pdf.cell(80, 7, 'Description', 1)
        elif layout == "compact":
            pdf.cell(100, 7, 'Description', 1)
            pdf.cell(30, 7, 'Qté', 1)
            pdf.cell(60, 7, 'Total', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        elif layout == "modern":
            pdf.cell(0, 10, 'DÉTAIL DES PRESTATIONS', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif layout == "minimal":
            pdf.cell(130, 7, 'Description', 1)
        pdf.cell(60, 7, 'Montant', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

        # Add items
        pdf.set_font(font, '', 10)

        total_ht = 0
        items_count = random.randint(3, 8)

        for _ in range(items_count):
            item = random.choice(item_options)
            qty = random.randint(1, 10)
            unit_price = round(random.uniform(10, 500), 2)
            item_total = qty * unit_price
            total_ht += item_total

        if layout == "standard" or layout == "detailed":
            pdf.cell(80, 7, item, 1)
            pdf.cell(25, 7, str(qty), 1, align='C')
            pdf.cell(40, 7, f'{unit_price:.2f} EUR', 1, align='R')
            pdf.cell(45, 7, f'{item_total:.2f} EUR', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        elif layout == "compact":
            pdf.cell(100, 7, f"{item} (x{qty})", 1)
            pdf.cell(30, 7, str(qty), 1, align='C')
            pdf.cell(60, 7, f'{item_total:.2f} EUR', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        elif layout == "modern":
            pdf.cell(0, 7, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.cell(130, 7, f"Quantité: {qty} x {unit_price:.2f} EUR", 0)
            pdf.cell(60, 7, f'{item_total:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            pdf.ln(3)
        elif layout == "minimal":
            pdf.cell(130, 7, item, 1)
            pdf.cell(60, 7, f'{item_total:.2f} EUR', 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

        # Calculate TVA and total TTC
        tva_rate = random.choice([5.5, 10, 20])
        tva = round(total_ht * (tva_rate / 100), 2)
        total_ttc = total_ht + tva

        # Totals
        pdf.ln(10)

        if layout != "modern":
            pdf.set_font(font, '', 11)
            pdf.cell(135, 7, 'Total HT:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
            pdf.cell(55, 7, f'{total_ht:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

            pdf.cell(135, 7, f'TVA ({tva_rate}%):', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
            pdf.cell(55, 7, f'{tva:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

            pdf.set_font(font, 'B', 12)
            pdf.cell(135, 10, 'Total TTC:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
            pdf.cell(55, 10, f'{total_ttc:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        else:
        # Modern layout has a different totals display
            pdf.ln(5)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font(font, '', 11)
            pdf.cell(135, 7, 'Total HT:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
            pdf.cell(55, 7, f'{total_ht:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

            pdf.cell(135, 8, f'TVA ({tva_rate}%):', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
            pdf.cell(55, 8, f'{tva:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

            pdf.set_font(font, 'B', 12)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(135, 10, 'Total TTC:', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='R', fill=1)
            pdf.cell(55, 10, f'{total_ttc:.2f} EUR', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R', fill=1)

            # Footer with payment information
            pdf.ln(15)
            pdf.set_font(font, '', 9)
            pdf.cell(0, 5, 'Paiement à réception de facture. Merci pour votre confiance.', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            if layout == "detailed":
                pdf.cell(0, 5, 'IBAN: FR76 3000 1007 1600 0000 9406 032', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                pdf.cell(0, 5, f'Facture émise le {date}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        # Output PDF
        pdf.output(pdf_path)
        return pdf_path
    
    def _convert_and_enhance(self, pdf_path, output_path, apply_defects=True, add_handwriting=False):
        """Convert PDF to image and apply enhancements/defects"""
        # Convert PDF to image
        images = convert_from_path(pdf_path)
        if not images:
            return
        
        # Get the first page
        img = images[0]
        
        # Convert to RGB mode if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply random rotation (slight skew)
        if random.random() < 0.6:
            angle = random.uniform(-2, 2)
            img = img.rotate(angle, expand=True)
        
        # Apply random brightness/contrast
        if random.random() < 0.7:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(random.uniform(0.85, 1.15))
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(random.uniform(0.9, 1.1))
        
        # If we should apply defects
        if apply_defects:
            img = self._apply_defects(img)
        
        # If we should add handwriting
        if add_handwriting:
            img = self._add_handwriting(img)
        
        # Apply some noise
        if random.random() < 0.5:
            img = self._add_noise(img)
        
        # Make sure the image is in RGB mode before saving as JPEG
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Save the enhanced image
        img.save(output_path)
    
    def _apply_defects(self, img):
        """Apply random defects like coffee stains, folds, or stamps"""
        img_rgba = img.convert('RGBA')
        defect_type = random.choice(['coffee_stains', 'folds', 'stamps', None])
        
        if defect_type and self.defect_assets[defect_type]:
            # Get a random defect image
            defect = random.choice(self.defect_assets[defect_type])
            
            # Resize to a random size but keep aspect ratio
            width, height = defect.size
            scale = random.uniform(0.2, 0.5)
            new_width = int(img_rgba.width * scale)
            new_height = int(new_width * (height / width))
            defect = defect.resize((new_width, new_height), Image.LANCZOS)
            
            # Position the defect at a random location
            x = random.randint(0, max(1, img_rgba.width - defect.width))
            y = random.randint(0, max(1, img_rgba.height - defect.height))
            
            # Paste the defect onto the image
            img_rgba.paste(defect, (x, y), defect)
        
        # Apply fold effect directly to the image
        if defect_type == 'folds' or random.random() < 0.3:
            img_rgba = self._apply_fold_effect(img_rgba)
        
        return img_rgba.convert('RGB')
    
    def _apply_fold_effect(self, img):
        """Apply a fold effect to the image"""
        # Choose fold direction (horizontal or vertical)
        is_horizontal = random.choice([True, False])
        
        # Create a fold line at a random position
        width, height = img.size
        if is_horizontal:
            fold_pos = random.randint(height // 4, 3 * height // 4)
            # Create a darkened line
            for x in range(width):
                for y in range(max(0, fold_pos-2), min(height, fold_pos+3)):
                    pixel = img.getpixel((x, y))
                    if len(pixel) == 4:  # RGBA
                        r, g, b, a = pixel
                        distance = abs(y - fold_pos)
                        darkening = max(0, (3 - distance) * 30)
                        img.putpixel((x, y), (
                            max(0, r - darkening),
                            max(0, g - darkening),
                            max(0, b - darkening),
                            a
                        ))
                    elif len(pixel) == 3:  # RGB
                        r, g, b = pixel
                        distance = abs(y - fold_pos)
                        darkening = max(0, (3 - distance) * 30)
                        img.putpixel((x, y), (
                            max(0, r - darkening),
                            max(0, g - darkening),
                            max(0, b - darkening)
                        ))
        else:
            fold_pos = random.randint(width // 4, 3 * width // 4)
            # Create a darkened line
            for y in range(height):
                for x in range(max(0, fold_pos-2), min(width, fold_pos+3)):
                    pixel = img.getpixel((x, y))
                    if len(pixel) == 4:  # RGBA
                        r, g, b, a = pixel
                        distance = abs(x - fold_pos)
                        darkening = max(0, (3 - distance) * 30)
                        img.putpixel((x, y), (
                            max(0, r - darkening),
                            max(0, g - darkening),
                            max(0, b - darkening),
                            a
                        ))
                    elif len(pixel) == 3:  # RGB
                        r, g, b = pixel
                        distance = abs(x - fold_pos)
                        darkening = max(0, (3 - distance) * 30)
                        img.putpixel((x, y), (
                            max(0, r - darkening),
                            max(0, g - darkening),
                            max(0, b - darkening)
                        ))
        
        return img
    
    def _add_handwriting(self, img):
            
        """Add handwritten annotations to the image"""
        img_rgba = img.convert('RGBA')
        
        if self.handwriting_assets:
            # Get a random handwriting image
            handwriting = random.choice(self.handwriting_assets)
            
            # Resize to a random size but keep aspect ratio
            width, height = handwriting.size
            scale = random.uniform(0.1, 0.3)  # Smaller than defects
            new_width = int(img_rgba.width * scale)
            new_height = int(new_width * (height / width))
            handwriting = handwriting.resize((new_width, new_height), Image.LANCZOS)
            
            # Position at a likely spot (near totals, client info, or margins)
            positioning = random.choice(['totals', 'client', 'margin'])
            
            if positioning == 'totals':
                # Bottom right - near totals
                x = img_rgba.width - handwriting.width - random.randint(10, 50)
                y = int(img_rgba.height * 0.7) + random.randint(0, 100)
            elif positioning == 'client':
                # Top right - near client info
                x = img_rgba.width - handwriting.width - random.randint(10, 50)
                y = int(img_rgba.height * 0.2) + random.randint(0, 100)
            else:
                # Random margin
                if random.choice([True, False]):
                    # Left or right margin
                    x = random.choice([
                        random.randint(5, 50),  # Left
                        img_rgba.width - handwriting.width - random.randint(5, 50)  # Right
                    ])
                    y = random.randint(50, img_rgba.height - handwriting.height - 50)
                else:
                    # Top or bottom margin
                    x = random.randint(50, img_rgba.width - handwriting.width - 50)
                    y = random.choice([
                        random.randint(5, 50),  # Top
                        img_rgba.height - handwriting.height - random.randint(5, 50)  # Bottom
                    ])
            
            # Paste the handwriting onto the image
            img_rgba.paste(handwriting, (x, y), handwriting)
        else:
            # Create a simple handwritten annotation with PIL
            draw = ImageDraw.Draw(img_rgba)
            note_text = random.choice([
                "Urgente!", "Payé", "À vérifier", "Voir avec comptabilité",
                "OK", "Archiver", "Traité le " + datetime.now().strftime("%d/%m"),
                "Appeler client"
            ])
            
            # Random position - likely in a margin or near totals
            x = random.choice([
                random.randint(10, 50),  # Left margin
                img_rgba.width - 150 - random.randint(10, 50)  # Right margin
            ])
            y = random.choice([
                random.randint(10, 50),  # Top margin
                img_rgba.height - 50 - random.randint(10, 50),  # Bottom margin
                int(img_rgba.height * 0.75) + random.randint(0, 50)  # Near totals
            ])
            
            # Draw text with a "handwriting" feel by adding slight randomness
            color = (0, 0, 255) if random.random() < 0.5 else (255, 0, 0)  # Blue or red pen
            angle = random.uniform(-5, 5)  # Slight angle to text
            
            # Create a temporary image for the rotated text
            text_layer = Image.new('RGBA', img_rgba.size, (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_layer)
            
            # Draw the text with a thicker "pen"
            for offset_x in range(-1, 2):
                for offset_y in range(-1, 2):
                    text_draw.text((x + offset_x, y + offset_y), note_text, fill=(*color, 150))
            
            # Rotate the text layer
            text_layer = text_layer.rotate(angle, resample=Image.BICUBIC, expand=False)
            
            # Composite the text layer onto the main image
            img_rgba = Image.alpha_composite(img_rgba, text_layer)
        
        return img_rgba

    def _add_noise(self, img):
        """Add random noise to the image to simulate scanner artifacts"""
        # Convert to numpy array
        img_array = np.array(img)
        
        # Add salt and pepper noise
        if random.random() < 0.3:
            # Salt (white) noise
            salt_mask = np.random.random(img_array.shape[:2]) < 0.01
            img_array[salt_mask] = 255
            
            # Pepper (black) noise
            pepper_mask = np.random.random(img_array.shape[:2]) < 0.01
            img_array[pepper_mask] = 0
        
        # Add Gaussian noise
        if random.random() < 0.4:
            # Convert to float for noise addition
            img_float = img_array.astype(np.float32)
            
            # Generate Gaussian noise
            noise_level = random.uniform(2, 10)
            noise = np.random.normal(0, noise_level, img_array.shape)
            
            # Add noise to image
            img_float += noise
            
            # Clip values to valid range
            img_array = np.clip(img_float, 0, 255).astype(np.uint8)
        
        # Apply slight blur to some images to simulate low-quality scans
        if random.random() < 0.2:
            # Use OpenCV for Gaussian blur
            blur_level = random.randint(1, 2)
            img_array = cv2.GaussianBlur(img_array, (blur_level*2+1, blur_level*2+1), 0)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)

    def create_non_invoice_documents(self, count=100, output_dir=None):
        """Generate non-invoice documents for negative samples"""
        print(f"Generating {count} non-invoice documents...")
        
        if output_dir is None:
            output_dir = os.path.join(self.output_base, "non_invoices")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Types of non-invoice documents to generate
        doc_types = ["letter", "memo", "report", "form"]
        
        for i in range(count):
            doc_type = random.choice(doc_types)
            if doc_type == "letter":
                self._generate_letter(os.path.join(output_dir, f"letter_{i+1}.jpg"))
            elif doc_type == "memo":
                self._generate_memo(os.path.join(output_dir, f"memo_{i+1}.jpg"))
            elif doc_type == "report":
                self._generate_report(os.path.join(output_dir, f"report_{i+1}.jpg"))
            else:  # form
                self._generate_form(os.path.join(output_dir, f"form_{i+1}.jpg"))
    
    def _generate_letter(self, output_path):
        """Generate a business letter"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(self.fonts)
        pdf.set_font(font, '', 12)
        
        # Sender info
        company = random.choice(self.company_names)
        pdf.cell(0, 10, company, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font, '', 10)
        pdf.cell(0, 5, fake.address().replace('\n', ', '), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, fake.phone_number(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Date
        pdf.ln(10)
        date = datetime.now().strftime("%d %B %Y")
        pdf.cell(0, 5, date, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        
        # Recipient
        pdf.ln(10)
        pdf.cell(0, 5, fake.name(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, fake.job_title(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, fake.company(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(0, 5, fake.address().replace('\n', ', '))
        
        # Subject
        pdf.ln(10)
        pdf.set_font(font, 'B', 11)
        pdf.cell(0, 8, f"Objet: {random.choice(['Demande de renseignements', 'Suivi de projet', 'Invitation', 'Confirmation de rendez-vous'])}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Content
        pdf.ln(5)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=5))
        pdf.ln(5)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # Closing
        pdf.ln(10)
        pdf.cell(0, 5, "Cordialement,", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
        pdf.cell(0, 5, fake.name(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, fake.job_title(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Save PDF to temp file
        temp_pdf = os.path.join(self.output_base, "temp", "temp_letter.pdf")
        os.makedirs(os.path.dirname(temp_pdf), exist_ok=True)
        pdf.output(temp_pdf)
        
        # Convert to image
        self._convert_and_enhance(temp_pdf, output_path, 
                                 apply_defects=random.random() < 0.3, 
                                 add_handwriting=random.random() < 0.2)
        
        # Remove temp file
        os.remove(temp_pdf)
    
    def _generate_memo(self, output_path):
        """Generate an internal memo"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(self.fonts)
        
        # Header
        pdf.set_font(font, 'B', 16)
        pdf.cell(0, 10, "NOTE DE SERVICE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Details in a box
        pdf.set_font(font, '', 11)
        pdf.set_fill_color(240, 240, 240)
        
        pdf.cell(40, 8, "Date:", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L', fill=1)
        pdf.cell(0, 8, datetime.now().strftime("%d/%m/%Y"), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        pdf.cell(40, 8, "De:", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L', fill=1)
        pdf.cell(0, 8, fake.name(), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        pdf.cell(40, 8, "À:", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L', fill=1)
        pdf.cell(0, 8, random.choice(["Tous les employés", "Service comptabilité", "Équipe marketing", "Direction"]), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        pdf.cell(40, 8, "Objet:", 1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L', fill=1)
        pdf.cell(0, 8, random.choice(["Réunion mensuelle", "Procédures de sécurité", "Nouveaux horaires", "Événement d'entreprise"]), 1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        # Content
        pdf.ln(10)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=4))
        pdf.ln(5)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # List of items if applicable
        if random.random() < 0.5:
            pdf.ln(5)
            for i in range(random.randint(3, 5)):
                pdf.cell(10, 6, "-", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.multi_cell(0, 6, fake.sentence())
        
        # Signature
        pdf.ln(15)
        pdf.cell(0, 6, fake.name(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 6, fake.job_title(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Save PDF to temp file
        temp_pdf = os.path.join(self.output_base, "temp", "temp_memo.pdf")
        os.makedirs(os.path.dirname(temp_pdf), exist_ok=True)
        pdf.output(temp_pdf)
        
        # Convert to image
        self._convert_and_enhance(temp_pdf, output_path, 
                                 apply_defects=random.random() < 0.3, 
                                 add_handwriting=random.random() < 0.2)
        
        # Remove temp file
        os.remove(temp_pdf)
    
    def _generate_report(self, output_path):
        """Generate a business report"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(self.fonts)
        
        # Title
        pdf.set_font(font, 'B', 16)
        report_type = random.choice(["RAPPORT D'ACTIVITÉ", "ANALYSE COMMERCIALE", "ÉTUDE DE MARCHÉ", "BILAN FINANCIER"])
        pdf.cell(0, 10, report_type, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Period
        pdf.set_font(font, 'I', 12)
        month = random.choice(["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
        year = random.randint(2020, 2024)
        pdf.cell(0, 8, f"{month} {year}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Executive summary
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 8, "Résumé exécutif", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=4))
        
        # Main sections
        sections = ["Résultats", "Analyse", "Perspectives"]
        
        for section in sections:
            pdf.ln(10)
            pdf.set_font(font, 'B', 14)
            pdf.cell(0, 8, section, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font(font, '', 11)
            pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=random.randint(3, 5)))
            
            # Add some bullet points
            if random.random() < 0.7:
                pdf.ln(5)
                for i in range(random.randint(2, 4)):
                    pdf.cell(10, 6, "-", 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.multi_cell(0, 6, fake.sentence())
        
        # Conclusion
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 8, "Conclusion", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # Save PDF to temp file
        temp_pdf = os.path.join(self.output_base, "temp", "temp_report.pdf")
        os.makedirs(os.path.dirname(temp_pdf), exist_ok=True)
        pdf.output(temp_pdf)
        
        # Convert to image
        self._convert_and_enhance(temp_pdf, output_path, 
                                 apply_defects=random.random() < 0.3, 
                                 add_handwriting=random.random() < 0.4)
        
        # Remove temp file
        os.remove(temp_pdf)
    
    def _generate_form(self, output_path):
        """Generate a generic form"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(self.fonts)
        
        # Form title
        pdf.set_font(font, 'B', 16)
        form_type = random.choice(["FORMULAIRE D'INSCRIPTION", "DEMANDE DE CONGÉS", "BON DE COMMANDE", "FICHE DE RENSEIGNEMENTS"])
        pdf.cell(0, 10, form_type, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        # Form fields
        pdf.ln(10)
        pdf.set_font(font, '', 11)
        
        # Common fields for most forms
        fields = [
            ("Nom:", fake.last_name()),
            ("Prénom:", fake.first_name()),
            ("Date de naissance:", fake.date_of_birth().strftime("%d/%m/%Y")),
            ("Adresse:", fake.street_address()),
            ("Ville:", fake.city()),
            ("Code Postal:", fake.postcode()),
            ("Email:", fake.email()),
            ("Téléphone:", fake.phone_number())
        ]
        
        # Add form-specific fields
        if "INSCRIPTION" in form_type:
            fields.extend([
                ("Formation souhaitée:", random.choice(["Développement Web", "Marketing Digital", "Comptabilité", "Management"])),
                ("Date souhaitée:", (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%d/%m/%Y"))
            ])
        elif "CONGÉS" in form_type:
            fields.extend([
                ("Date de début:", (datetime.now() + timedelta(days=random.randint(10, 30))).strftime("%d/%m/%Y")),
                ("Date de fin:", (datetime.now() + timedelta(days=random.randint(31, 45))).strftime("%d/%m/%Y")),
                ("Type de congés:", random.choice(["Congés payés", "RTT", "Congé sans solde", "Congé parental"]))
            ])
        elif "COMMANDE" in form_type:
            fields.extend([
                ("Référence produit:", f"REF-{random.randint(1000, 9999)}"),
                ("Quantité:", str(random.randint(1, 20))),
                ("Date de livraison souhaitée:", (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%d/%m/%Y"))
            ])
        
        # Draw form fields
        pdf.set_fill_color(240, 240, 240)
        for label, value in fields:
            pdf.set_font(font, 'B', 11)
            pdf.cell(50, 8, label, 0, 0)
            pdf.set_font(font, '', 11)
            
            # Either pre-filled or empty
            if random.random() < 0.4:
                pdf.cell(0, 8, value, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                pdf.cell(0, 8, "________________", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Signature area
        pdf.ln(15)
        pdf.cell(0, 8, "Date: ________________", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, "Signature:", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(80, 20, "", 1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        # Save PDF to temp file
        temp_pdf = os.path.join(self.output_base, "temp", "temp_form.pdf")
        os.makedirs(os.path.dirname(temp_pdf), exist_ok=True)
        pdf.output(temp_pdf)
        
        # Convert to image with more handwriting (forms often have handwriting)
        self._convert_and_enhance(temp_pdf, output_path, 
                                 apply_defects=random.random() < 0.3, 
                                 add_handwriting=random.random() < 0.6)
        
        # Remove temp file
        os.remove(temp_pdf)

def main():
    """Main function to run the invoice generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate invoice dataset for document understanding")
    parser.add_argument("-n", "--num", type=int, default=100, help="Number of invoices to generate")
    parser.add_argument("--non-invoices", type=int, default=20, help="Number of non-invoice documents to generate")
    parser.add_argument("--output", type=str, default="dataset", help="Output directory")
    parser.add_argument("--only-invoices", action="store_true", help="Only generate invoices (no non-invoices)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
        
    # Create generator
    generator = InvoiceGenerator()
    
    # Override output base if specified
    if args.output != "dataset":
        generator.output_base = args.output
        # Update dirs
        generator.dirs = {
            "original": os.path.join(generator.output_base, "original"),
            "training": os.path.join(generator.output_base, "training"),
            "validation": os.path.join(generator.output_base, "validation"),
            "test": os.path.join(generator.output_base, "test"),
            "sample": os.path.join(generator.output_base, "sample")
        }
        # Create directories
        for dir_name in generator.dirs.values():
            os.makedirs(dir_name, exist_ok=True)
    
    # Generate invoice dataset
    generator.generate_dataset(count=args.num)
    
    # Generate non-invoice documents unless disabled
    if not args.only_invoices:
        generator.create_non_invoice_documents(count=args.non_invoices)
    
    print(f"Dataset generation complete. Files saved to {generator.output_base}/")
    
    # Print summary
    print("\nDataset Summary:")
    for dir_name, dir_path in generator.dirs.items():
        files = list(Path(dir_path).glob("*.jpg")) + list(Path(dir_path).glob("*.jpeg")) + list(Path(dir_path).glob("*.pdf"))
        print(f"  {dir_name}: {len(files)} files")
    
    if not args.only_invoices:
        non_invoice_dir = os.path.join(generator.output_base, "non_invoices")
        non_invoice_files = list(Path(non_invoice_dir).glob("*.jpg")) + list(Path(non_invoice_dir).glob("*.jpeg")) + list(Path(non_invoice_dir).glob("*.pdf"))
        print(f"  non_invoices: {len(non_invoice_files)} files")

if __name__ == "__main__":
    main()