from faker import Faker
from fpdf import FPDF, XPos, YPos
import random
from datetime import datetime, timedelta
import os
from PIL import Image, ImageEnhance
from pdf2image import convert_from_path
import numpy as np

# Initialiser Faker en français
fake = Faker(['fr_FR'])

class InvoiceGenerator:
    def __init__(self):
        # Entreprises de bricolage
        self.diy_companies = [
            "LEROY MERLIN", "CASTORAMA", "BRICORAMA", "BRICO DÉPÔT",
            "BRICOMARCHÉ", "MR BRICOLAGE", "WELDOM", "BRICOMAN"
        ]
        
        # Entreprises tech
        self.tech_companies = [
            "Tech Solutions SARL", "InfoSys France", "Digital Services SA",
            "Consulting Pro EURL", "Web Expert SAS", "Data Analytics SARL",
            "Cloud Systems SAS", "Smart IT Services"
        ]
        
        # Grande distribution
        self.retail_companies = [
            "CARREFOUR", "AUCHAN", "E.LECLERC", "INTERMARCHÉ",
            "SUPER U", "LIDL FRANCE", "CASINO", "MONOPRIX"
        ]
        
        # Tous les noms d'entreprises
        self.company_names = self.diy_companies + self.tech_companies + self.retail_companies
        
        # Styles par type d'entreprise
        self.company_styles = {
            # Bricolage
            "LEROY MERLIN": {"color": (67, 176, 42), "header": "BRICOLAGE - CONSTRUCTION - DÉCORATION - JARDINAGE"},
            "CASTORAMA": {"color": (0, 84, 166), "header": "BRICOLAGE - CONSTRUCTION - DÉCORATION - JARDINAGE"},
            
            # Tech
            "Tech Solutions SARL": {"color": (41, 128, 185), "header": "DÉVELOPPEMENT - CONSEIL - FORMATION - SUPPORT"},
            "InfoSys France": {"color": (52, 152, 219), "header": "SOLUTIONS - SERVICES - INNOVATION - TECHNOLOGIE"},
            
            # Distribution
            "CARREFOUR": {"color": (0, 0, 255), "header": "ALIMENTATION - MAISON - MODE - LOISIRS"},
            "AUCHAN": {"color": (227, 30, 45), "header": "HYPERMARCHÉ - SUPERMARCHÉ - DRIVE - PROXIMITÉ"}
        }
        
        # Articles par secteur
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
        
        # Polices et layouts
        self.fonts = ["Helvetica"]
        self.layouts = ["standard", "modern"]
        
        # Ajouter des palettes de couleurs
        self.color_schemes = {
            "blue": {
                "header": (41, 128, 185),
                "accent": (52, 152, 219),
                "table_header": (236, 240, 241),
                "table_stripe": (245, 247, 248)
            },
            "green": {
                "header": (39, 174, 96),
                "accent": (46, 204, 113),
                "table_header": (236, 240, 241),
                "table_stripe": (245, 247, 248)
            },
            "red": {
                "header": (192, 57, 43),
                "accent": (231, 76, 60),
                "table_header": (236, 240, 241),
                "table_stripe": (245, 247, 248)
            },
            "purple": {
                "header": (142, 68, 173),
                "accent": (155, 89, 182),
                "table_header": (236, 240, 241),
                "table_stripe": (245, 247, 248)
            },
            "orange": {
                "header": (211, 84, 0),
                "accent": (230, 126, 34),
                "table_header": (236, 240, 241),
                "table_stripe": (245, 247, 248)
            }
        }
        
    def set_style(self, pdf):
        """
        Définit le style aléatoire pour la facture
        """
        # Choisir un style aléatoire
        layout = random.choice(self.layouts)
        color_scheme = random.choice(list(self.color_schemes.values()))
        
        # Variations de style
        style = {
            "font": "Helvetica",
            "layout": layout,
            "header_size": random.choice([14, 16, 18, 20]),
            "text_size": random.choice([10, 11, 12]),
            "line_height": random.choice([6, 7, 8, 9, 10]),
            "table_style": random.choice(["simple", "grid", "striped"]),
            "alignment": random.choice(["L", "C"]),
            "spacing": random.randint(5, 15),
            "border": random.choice([0, 1]),
            "fill": random.choice([True, False]),
            "colors": color_scheme
        }
        
        return style
        
    def generate_invoice_number(self):
        prefix = random.choice(["FACT", "INV", "F", "FA"])
        year = str(random.randint(2023, 2024))
        number = str(random.randint(1000, 9999))
        separator = random.choice(["-", "/", "_"])
        return f"{prefix}{separator}{year}{separator}{number}"
    
    def generate_items(self, items_list):
        """
        Génère une liste d'articles à partir d'une liste spécifique au secteur
        """
        items = []
        for _ in range(random.randint(2, 8)):
            service = random.choice(items_list)
            quantity = random.randint(1, 20)
            unit_price = round(random.uniform(50, 2000), 2)
            total = round(quantity * unit_price, 2)
            
            items.append({
                "description": service,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            })
        
        return items

    def create_pdf(self, output_path):
        # Création du PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Obtenir le style
        style = self.set_style(pdf)
        
        # Choisir une entreprise et son style
        company = random.choice(self.company_names)
        company_style = self.company_styles.get(company, {
            "color": (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
            "header": "PRODUITS - SERVICES - SOLUTIONS - QUALITÉ"
        })
        
        # Appliquer les couleurs de l'en-tête
        r, g, b = style["colors"]["header"]
        pdf.set_fill_color(r, g, b)
        pdf.rect(0, 0, 210, 20, 'F')
        
        # En-tête de la facture avec style
        pdf.set_font("Helvetica", "B", style["header_size"])
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, style["line_height"], company, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=style["alignment"])
        
        # Réinitialiser la couleur du texte pour le contenu
        pdf.set_text_color(0, 0, 0)
        
        # Informations de l'entreprise
        pdf.set_font("Helvetica", size=style["text_size"])
        address_info = [
            f"{fake.street_address()}",
            f"{fake.postcode()} {fake.city()}",
            f"Tél: {fake.phone_number()}",
            f"Email: {fake.email()}"
        ]
        
        for info in address_info:
            pdf.cell(0, style["line_height"], info, ln=True, align=style["alignment"])
        
        # Numéro de facture et date avec espacement personnalisé
        pdf.ln(style["spacing"])
        invoice_number = self.generate_invoice_number()
        date = fake.date_between(start_date='-1y', end_date='today')
        
        pdf.set_font("Helvetica", "B", style["text_size"])
        pdf.cell(0, style["line_height"], f"Facture N°: {invoice_number}", ln=True)
        pdf.cell(0, style["line_height"], f"Date: {date.strftime('%d/%m/%Y')}", ln=True)
        
        # Informations client avec style
        pdf.ln(style["spacing"])
        pdf.cell(0, style["line_height"], "Facturé à:", ln=True)
        client_info = [
            f"MR {fake.last_name().upper()} {fake.first_name()}",
            fake.street_address(),
            f"{fake.postcode()} {fake.city()}"
        ]
        
        for info in client_info:
            pdf.cell(0, style["line_height"], info, ln=True)
        
        # Tableau des articles avec style
        pdf.ln(style["spacing"])
        
        # Sélectionner les articles selon le type d'entreprise
        if company in self.diy_companies:
            items = self.generate_items(self.diy_items)
        elif company in self.tech_companies:
            items = self.generate_items(self.tech_items)
        else:
            items = self.generate_items(self.retail_items)
        
        # En-têtes du tableau avec style
        headers = ["Description", "Quantité", "Prix unitaire", "Total"]
        col_widths = [80, 30, 40, 40]
        
        # Style du tableau
        if style["table_style"] == "striped":
            r, g, b = style["colors"]["table_header"]
            pdf.set_fill_color(r, g, b)
        
        # En-têtes
        pdf.set_font("Helvetica", "B", style["text_size"])
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], style["line_height"], header, 1, 0, "C", True)
        pdf.ln()
        
        # Contenu du tableau avec alternance de couleurs
        pdf.set_font("Helvetica", "", style["text_size"])
        total_amount = 0
        for idx, item in enumerate(items):
            if style["table_style"] == "striped" and idx % 2 == 0:
                r, g, b = style["colors"]["table_stripe"]
                pdf.set_fill_color(r, g, b)
                fill = True
            else:
                fill = False
            
            pdf.cell(col_widths[0], style["line_height"], item["description"], 1, 0, fill=fill)
            pdf.cell(col_widths[1], style["line_height"], str(item["quantity"]), 1, 0, "C", fill=fill)
            pdf.cell(col_widths[2], style["line_height"], f"{item['unit_price']:.2f} EUR", 1, 0, "R", fill=fill)
            pdf.cell(col_widths[3], style["line_height"], f"{item['total']:.2f} EUR", 1, 1, "R", fill=fill)
            total_amount += item["total"]
        
        # Totaux avec style
        pdf.ln(style["spacing"])
        pdf.set_font("Helvetica", "B", style["text_size"])
        
        # TVA avec taux variable
        tva_rate = random.choice([5.5, 10.0, 20.0])
        tva_amount = total_amount * (tva_rate / 100)
        total_ttc = total_amount + tva_amount
        
        pdf.cell(0, style["line_height"], f"Total HT: {total_amount:.2f} EUR", ln=True, align="R")
        pdf.cell(0, style["line_height"], f"TVA ({tva_rate}%): {tva_amount:.2f} EUR", ln=True, align="R")
        pdf.cell(0, style["line_height"], f"Total TTC: {total_ttc:.2f} EUR", ln=True, align="R")
        
        # Mentions légales avec style
        pdf.ln(style["spacing"])
        pdf.set_font("Helvetica", size=8)
        pdf.cell(0, 5, "Nos Conditions Générales de ventes sont disponible", ln=True, align="C")
        siret = random.randint(10000000000000, 99999999999999)
        tva = random.randint(10000000000, 99999999999)
        pdf.cell(0, 5, f"SIRET: {siret} - TVA Intra: FR{tva}", ln=True, align="C")
        
        pdf.output(output_path)

    def create_mixed_format(self, output_path, format_type=None):
        """
        Crée une facture dans le format spécifié (PDF, JPEG, ou JPG)
        """
        try:
            # Si aucun format n'est spécifié, en choisir un aléatoirement
            if format_type is None:
                format_type = random.choice(['pdf', 'jpeg', 'jpg'])
            
            # Créer d'abord en PDF
            temp_pdf_path = output_path + '.temp.pdf'
            self.create_pdf(temp_pdf_path)
            
            if format_type == 'pdf':
                # Renommer simplement le fichier temporaire
                if os.path.exists(temp_pdf_path):
                    os.rename(temp_pdf_path, output_path)
                    return True
            else:
                # Convertir en image
                try:
                    poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
                    images = convert_from_path(temp_pdf_path, poppler_path=poppler_path)
                    if images:
                        # Toujours utiliser 'JPEG' comme format, même pour .jpg
                        quality = random.randint(75, 95)
                        images[0].save(output_path, 'JPEG', quality=quality)
                        os.remove(temp_pdf_path)
                        return True
                except Exception as e:
                    print(f"Erreur lors de la conversion en {format_type}: {str(e)}")
                    # En cas d'erreur, garder le PDF
                    if os.path.exists(temp_pdf_path):
                        os.rename(temp_pdf_path, output_path.replace(f'.{format_type}', '.pdf'))
                        return True
            return False
        except Exception as e:
            print(f"Erreur lors de la création du fichier: {str(e)}")
            return False

def augment_invoice(file_path, output_dir):
    """
    Augmente une facture en créant plusieurs variations
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        extension = os.path.splitext(file_path)[1].lower()
        
        # Différent traitement selon le type de fichier
        if extension == '.pdf':
            # Pour les PDF, utiliser pdf2image
            poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
            images = convert_from_path(file_path, poppler_path=poppler_path)
            source_image = images[0]
        else:
            # Pour les images (jpg, jpeg), charger directement
            source_image = Image.open(file_path)
        
        # Créer plusieurs variations
        for variation in range(3):  # 3 variations par facture
            # Copie de l'image pour la manipulation
            img = source_image.copy()
            
            # 1. Rotation aléatoire
            angle = random.uniform(-5, 5)
            img = img.rotate(angle, expand=True)
            
            # 2. Variation de luminosité
            enhancer = ImageEnhance.Brightness(img)
            factor = random.uniform(0.8, 1.2)
            img = enhancer.enhance(factor)
            
            # 3. Variation de contraste
            enhancer = ImageEnhance.Contrast(img)
            factor = random.uniform(0.8, 1.2)
            img = enhancer.enhance(factor)
            
            # 4. Ajout de bruit (optionnel)
            if random.random() < 0.3:
                img_array = np.array(img)
                noise = np.random.normal(0, 5, img_array.shape)
                noisy_img = img_array + noise
                noisy_img = np.clip(noisy_img, 0, 255)
                img = Image.fromarray(noisy_img.astype('uint8'))
            
            # 5. Qualité de compression variable
            quality = random.randint(60, 95)
            
            # Sauvegarder la variation
            output_path = os.path.join(
                output_dir, 
                f"{base_name}_aug_{variation + 1}.jpg"
            )
            img.save(output_path, 'JPEG', quality=quality)
            
            print(f"Variation {variation + 1} générée pour {base_name}")
                
    except Exception as e:
        print(f"Erreur lors de l'augmentation de {file_path}: {str(e)}")

def generate_dataset(num_invoices, base_dir):
    """
    Génère le dataset complet avec différents formats
    """
    # Créer les répertoires nécessaires
    original_dir = os.path.join(base_dir, "original")
    augmented_dir = os.path.join(base_dir, "augmented")
    
    for dir_path in [original_dir, augmented_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # Générer les factures
    generator = InvoiceGenerator()
    
    print(f"Génération de {num_invoices} factures...")
    successful_files = 0
    
    for i in range(num_invoices):
        try:
            # Choisir un format aléatoire
            format_type = random.choice(['pdf', 'jpeg', 'jpg'])
            extension = format_type.lower()
            
            # Chemin du fichier avec l'extension appropriée
            original_path = os.path.join(original_dir, f"facture_{i+1}.{extension}")
            
            # Créer la facture dans le format choisi
            if generator.create_mixed_format(original_path, format_type):
                # Vérifier que le fichier existe avant d'essayer de l'augmenter
                if os.path.exists(original_path):
                    augment_invoice(original_path, augmented_dir)
                    successful_files += 1
                    print(f"Facture {i+1} générée et augmentée avec succès")
            
            if (i + 1) % 10 == 0:
                print(f"Progression: {i + 1}/{num_invoices} factures traitées ({successful_files} réussies)")
                
        except Exception as e:
            print(f"Erreur lors du traitement de la facture {i+1}: {str(e)}")
            continue
    
    print(f"\nGénération terminée: {successful_files}/{num_invoices} factures générées avec succès")

if __name__ == "__main__":
    # Générer 5000 factures avec formats mixtes
    generate_dataset(10, "dataset") 