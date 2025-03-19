from faker import Faker
from fpdf import FPDF
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
        self.company_names = [
            "Tech Solutions SARL", "InfoSys France", "Digital Services SA",
            "Consulting Pro EURL", "Web Expert SAS", "Data Analytics SARL",
            "Cloud Systems SAS", "Smart IT Services", "Digital Factory EURL"
        ]
        
        self.fonts = ["Helvetica", "Times", "Courier"]
        self.layouts = ["standard", "compact", "modern"]
        self.colors = {
            "black": (0, 0, 0),
            "dark_blue": (0, 0, 139),
            "dark_green": (0, 100, 0),
            "dark_grey": (69, 69, 69),
            "purple": (128, 0, 128)
        }
        
        # Ajouter plus de variations
        self.company_names.extend([
            "Global Services", "Euro Tech", "Media Plus",
            "Consulting Group", "IT Solutions", "Data Corp",
            # Ajouter 20-30 noms d'entreprises supplémentaires
        ])
        
        # Ajouter plus de services
        self.services = [
            "Développement web", "Maintenance", "Formation",
            "Consultation", "Support technique", "Hébergement",
            "Design UX/UI", "SEO", "Développement mobile",
            "Analyse de données", "Cloud Computing", "Sécurité IT",
            "Gestion de projet", "Infrastructure réseau", "Audit système"
        ]
        
        # Ajouter des variations de mise en page
        self.layouts.extend(["minimal", "premium", "classic"])
        
    def set_style(self, pdf):
        # Choisir un style aléatoire
        layout = random.choice(self.layouts)
        main_font = random.choice(self.fonts)
        color = random.choice(list(self.colors.values()))
        pdf.set_text_color(*color)
        
        return {
            "font": main_font,
            "layout": layout,
            "color": color,
            "header_size": random.choice([14, 16, 18]),
            "text_size": random.choice([10, 11, 12]),
            "line_height": random.choice([6, 8, 10])
        }
        
    def generate_invoice_number(self):
        prefix = random.choice(["FACT", "INV", "F", "FA"])
        year = str(random.randint(2023, 2024))
        number = str(random.randint(1000, 9999))
        separator = random.choice(["-", "/", "_"])
        return f"{prefix}{separator}{year}{separator}{number}"
    
    def generate_items(self):
        items = []
        for _ in range(random.randint(2, 8)):
            service = random.choice(self.services)
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
        # Création du PDF avec orientation aléatoire
        orientation = random.choice(['P', 'L']) if random.random() < 0.2 else 'P'
        pdf = FPDF(orientation=orientation)
        pdf.add_page()
        
        # Appliquer un style aléatoire
        style = self.set_style(pdf)
        
        # En-tête de la facture
        company = random.choice(self.company_names)
        invoice_number = self.generate_invoice_number()
        date = fake.date_between(start_date='-1y', end_date='today')
        
        if style["layout"] == "modern":
            # Style moderne avec bande colorée
            pdf.set_fill_color(*style["color"])
            pdf.rect(0, 0, pdf.w, 30, 'F')
            pdf.set_text_color(255, 255, 255)
        
        # Informations de l'entreprise
        pdf.set_font(style["font"], "B", style["header_size"])
        
        if style["layout"] == "compact":
            # Style compact
            pdf.cell(0, style["line_height"], company, ln=True)
            pdf.set_font(style["font"], size=style["text_size"])
            company_info = [
                f"{fake.street_address()}, {fake.postcode()} {fake.city()}",
                f"Tél: {fake.phone_number()} | Email: {fake.email()}"
            ]
        else:
            # Style standard ou moderne
            pdf.cell(0, style["line_height"], company, ln=True)
            pdf.set_font(style["font"], size=style["text_size"])
            company_info = [
                fake.street_address(),
                f"{fake.postcode()} {fake.city()}",
                f"Tél: {fake.phone_number()}",
                f"Email: {fake.email()}"
            ]
        
        if style["layout"] == "modern":
            pdf.set_text_color(*style["color"])
            
        for info in company_info:
            pdf.cell(0, style["line_height"], info, ln=True)
        
        # Numéro de facture et date
        pdf.ln(5)
        pdf.set_font(style["font"], "B", style["text_size"])
        
        # Disposition variable des informations de facture
        if random.random() < 0.5:
            pdf.cell(0, style["line_height"], f"Facture N°: {invoice_number}", ln=True)
            pdf.cell(0, style["line_height"], f"Date: {date.strftime('%d/%m/%Y')}", ln=True)
        else:
            pdf.cell(pdf.w/2, style["line_height"], f"Facture N°: {invoice_number}")
            pdf.cell(pdf.w/2, style["line_height"], f"Date: {date.strftime('%d/%m/%Y')}", ln=True)
        
        # Informations du client avec mise en page variable
        pdf.ln(5)
        if random.random() < 0.3:
            # Style encadré
            pdf.rect(pdf.get_x(), pdf.get_y(), 80, 30)
            
        pdf.cell(0, style["line_height"], "Facturé à:", ln=True)
        pdf.set_font(style["font"], size=style["text_size"])
        client_info = [
            fake.company(),
            fake.street_address(),
            f"{fake.postcode()} {fake.city()}"
        ]
        
        for info in client_info:
            pdf.cell(0, style["line_height"], info, ln=True)
        
        # Tableau des articles
        pdf.ln(10)
        items = self.generate_items()
        
        # En-têtes du tableau avec style variable
        headers = ["Description", "Quantité", "Prix unitaire", "Total"]
        if orientation == 'P':
            col_widths = [80, 30, 40, 40] if style["layout"] != "compact" else [70, 25, 35, 35]
        else:
            col_widths = [120, 40, 50, 50]
            
        # Style du tableau variable
        pdf.set_font(style["font"], "B", style["text_size"])
        pdf.set_fill_color(*[int(c * 0.9) for c in style["color"]])
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], style["line_height"], header, 1, 0, 'C', True)
        pdf.ln()
        
        # Contenu du tableau
        pdf.set_font(style["font"], size=style["text_size"])
        total_amount = 0
        
        for item in items:
            # Alternance de couleurs pour les lignes
            if random.random() < 0.3:
                pdf.set_fill_color(240, 240, 240)
                fill = True
            else:
                fill = False
                
            pdf.cell(col_widths[0], style["line_height"], item["description"], 1, 0, fill=fill)
            pdf.cell(col_widths[1], style["line_height"], str(item["quantity"]), 1, 0, 'C', fill=fill)
            pdf.cell(col_widths[2], style["line_height"], f"{item['unit_price']:.2f} EUR", 1, 0, 'R', fill=fill)
            pdf.cell(col_widths[3], style["line_height"], f"{item['total']:.2f} EUR", 1, 1, 'R', fill=fill)
            total_amount += item["total"]
        
        # Total avec variation aléatoire des champs affichés
        pdf.ln(5)
        
        # Position des totaux variable
        totals_x = pdf.w - 80 if random.random() < 0.7 else pdf.get_x()
        pdf.set_x(totals_x)
        
        # Choisir aléatoirement quels totaux afficher
        show_ht = random.choice([True, True, True])
        show_tva = random.choice([True, True, False])
        show_ttc = random.choice([True, True, True])
        
        if not any([show_ht, show_tva, show_ttc]):
            show_ttc = True
        
        # Style des totaux
        if random.random() < 0.3:
            pdf.set_fill_color(240, 240, 240)
            fill = True
        else:
            fill = False
            
        # Afficher les totaux sélectionnés
        if show_ht:
            pdf.cell(0, style["line_height"], f"Total HT: {total_amount:.2f} EUR", ln=True, fill=fill)
        
        # Varier le taux de TVA
        tva_rate = random.choice([19.6, 20.0, 5.5, 10.0])
        tva_amount = total_amount * (tva_rate / 100)
        
        if show_tva:
            pdf.set_x(totals_x)
            pdf.cell(0, style["line_height"], f"TVA ({tva_rate}%): {tva_amount:.2f} EUR", ln=True, fill=fill)
        
        if show_ttc:
            pdf.set_x(totals_x)
            total_ttc = total_amount + tva_amount
            pdf.set_font(style["font"], "B", style["text_size"])
            pdf.cell(0, style["line_height"], f"Total TTC: {total_ttc:.2f} EUR", ln=True, fill=fill)
        
        # Mentions légales aléatoires
        if random.random() < 0.7:
            pdf.ln(10)
            pdf.set_font(style["font"], "I", style["text_size"] - 2)
            mentions = [
                "TVA intracommunautaire: FR" + str(random.randint(10000000000, 99999999999)),
                "SIRET: " + str(random.randint(10000000000000, 99999999999999)),
                "Payable sous 30 jours",
                "En cas de retard de paiement, une pénalité de 3 fois le taux légal sera appliquée"
            ]
            if random.random() < 0.5:
                random.shuffle(mentions)
            for mention in mentions[:random.randint(1, len(mentions))]:
                pdf.cell(0, style["line_height"] - 2, mention, ln=True)
        
        # Sauvegarde du PDF
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
    generate_dataset(5000, "dataset") 