from fpdf import FPDF, XPos, YPos
import random
import os
from datetime import datetime
from PIL import Image, ImageEnhance
from invoice_generator.config import FONTS, COLORS, VAT_RATES
from invoice_generator.data_provider import fake

class InvoicePDF:
    def __init__(self, data_provider=None):
        self.data_provider = data_provider
        # Vérifier la disponibilité de la police Unicode
        font_path = os.path.join('fonts', 'DejaVuSans.ttf')
        self.has_unicode_font = os.path.exists(font_path)
        if not self.has_unicode_font:
            print("Note: Police DejaVuSans non trouvée dans le dossier 'fonts'. Le symbole € sera remplacé par EUR.")
    
    def generate_invoice_pdf(self, company_name, company_type, invoice_num, date,
                        client_name, client_address, item_options, layout, output_path):
        """Generate a PDF invoice with the given parameters"""
        # Initialize PDF with random orientation
        orientation = 'P' if random.random() < 0.9 else 'L'  # 10% de chance d'être en paysage
        pdf = FPDF(orientation=orientation)
        
        # Ajouter la police Unicode si disponible
        unicode_font = None
        if self.has_unicode_font:
            try:
                pdf.add_font('DejaVuSans', '', os.path.join('fonts', 'DejaVuSans.ttf'), uni=True)
                unicode_font = 'DejaVuSans'
            except Exception as e:
                print(f"Erreur lors du chargement de la police Unicode: {e}")
                
        # Décider aléatoirement quel format de devise utiliser pour cette facture
        use_euro_symbol = random.random() < 0.6  # 60% de chance d'utiliser € si disponible
        
        # Ne pas utiliser le symbole € si la police Unicode n'est pas disponible
        if not unicode_font:
            use_euro_symbol = False
            
        # NOUVELLE FONCTION: Dessiner un prix avec le symbole € ou "EUR"
        def draw_price_cell(w, h, amount, border=1, ln=0, align='R', fill=False):
            """
            Dessine une cellule avec un prix formaté en utilisant la bonne police pour le symbole €
            
            Args:
                w: largeur de la cellule
                h: hauteur de la cellule
                amount: montant à afficher
                border: 0=pas de bordure, 1=bordure
                ln: 0=à droite, 1=début de la ligne suivante
                align: alignement (L, C, R)
                fill: remplissage (background)
            """
            if use_euro_symbol and unicode_font:
                # Format du montant sans symbole
                price_text = f"{amount:.2f} "
                
                # Calculer la largeur du texte
                price_width = pdf.get_string_width(price_text)
                euro_width = 5  # estimation de la largeur du symbole €
                
                # Sauvegarder la position actuelle
                x = pdf.get_x()
                y = pdf.get_y()
                
                # Dessiner la cellule de fond et la bordure si nécessaire
                if fill or border:
                    pdf.rect(x, y, w, h, style=('F' if fill else '') + ('D' if border else ''))
                
                # Calculer la position du texte selon l'alignement
                if align == 'R':
                    text_x = x + w - price_width - euro_width - 2  # 2px de marge
                elif align == 'C':
                    text_x = x + (w - price_width - euro_width) / 2
                else:  # 'L'
                    text_x = x + 2  # 2px de marge
                
                # Dessiner le montant avec la police standard
                pdf.set_xy(text_x, y + (h - pdf.font_size) / 2)
                pdf.write(h, price_text)
                
                # Dessiner le symbole € avec la police Unicode
                current_font = pdf.font_family
                current_style = pdf.font_style
                current_size = pdf.font_size_pt
                
                pdf.set_font(unicode_font, '', current_size)
                pdf.set_xy(text_x + price_width, y + (h - pdf.font_size) / 2)
                pdf.write(h, "€")
                
                # Restaurer la police d'origine
                pdf.set_font(current_font, current_style, current_size)
                
                # Avancer à la position suivante
                if ln == 1:
                    pdf.ln(h)
                else:
                    pdf.set_xy(x + w, y)
            else:
                # Version simple avec "EUR"
                pdf.cell(w, h, f"{amount:.2f} EUR", border, ln, align, fill)
        
        pdf.add_page()

        # Choose random style elements
        font = random.choice(FONTS)
        color = random.choice(list(COLORS.values()))
        header_size = random.choice([14, 16, 18])
        text_size = random.choice([10, 11, 12])
        line_height = random.choice([6, 7, 8])

        # Set style based on layout
        if layout == "modern":
            # Style moderne avec bande colorée
            pdf.set_fill_color(*color)
            pdf.rect(0, 0, pdf.w, 30, 'F')
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(*color)

        # Company header
        company_style = self.data_provider.company_styles.get(company_name, {"color": color, "header": ""})
        pdf.set_font(font, 'B', header_size)
        pdf.cell(0, 10, company_name, ln=True, align='C')
        
        # Company info - différents formats selon le layout
        pdf.set_font(font, '', 10)
        if layout == "compact":
            address = "123 Rue de Paris, 75001 Paris"
            pdf.cell(0, 5, address, ln=True, align='C')
            pdf.cell(0, 5, f"Tel: {fake.phone_number()} | Email: {fake.email()}", ln=True, align='C')
        else:
            pdf.cell(0, 5, fake.street_address(), ln=True, align='C')
            pdf.cell(0, 5, f"{fake.postcode()} {fake.city()}", ln=True, align='C')
            pdf.cell(0, 5, f"Tel: {fake.phone_number()}", ln=True, align='C')

        # Reset text color to black for the rest
        pdf.set_text_color(0, 0, 0)

        # Invoice details - disposition variable
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 10, 'FACTURE', ln=True)

        # Variable placement of invoice number and date
        pdf.set_font(font, '', text_size)
        if random.random() < 0.5:
            pdf.cell(0, 7, f'N° Facture: {invoice_num}', ln=True)
            pdf.cell(0, 7, f'Date: {date}', ln=True)
        else:
            pdf.cell(pdf.w/2, 7, f'N° Facture: {invoice_num}', 0, 0)
            pdf.cell(pdf.w/2, 7, f'Date: {date}', 0, 1, align='R')

        # Client information - optionally boxed
        pdf.ln(5)
        client_box = random.random() < 0.3
        start_y = pdf.get_y()
        
        pdf.set_font(font, 'B', 12)
        pdf.cell(0, 8, 'Client:', ln=True)
        pdf.set_font(font, '', text_size)
        pdf.cell(0, 6, client_name, ln=True)
        pdf.multi_cell(0, 6, client_address)
        
        # Draw box around client info if selected
        if client_box:
            end_y = pdf.get_y()
            pdf.rect(10, start_y, 90, end_y - start_y)

        # Items table with variable header colors
        pdf.ln(10)
        headers = ["Description", "Qté", "Prix unitaire", "Total"]
        
        # Adjust column widths based on orientation
        if orientation == 'P':  # Portrait
            col_widths = [90, 20, 40, 40] if layout != "compact" else [75, 20, 35, 35]
        else:  # Landscape
            col_widths = [130, 30, 50, 50]
        
        # Header style with various colors
        header_color = (
            min(color[0] + 30, 255),
            min(color[1] + 30, 255),
            min(color[2] + 30, 255)
        )
        pdf.set_fill_color(*header_color)
        
        # Draw headers
        pdf.set_font(font, 'B', text_size)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        # Draw items with alternating row colors
        pdf.set_font(font, '', text_size)
        total = 0
        
        # Process items
        for i, item in enumerate(item_options):
            # Alternating row colors with some randomness
            if i % 2 == 1 and random.random() < 0.7:
                pdf.set_fill_color(245, 245, 245)
                fill = True
            else:
                fill = False
                
            # Calculate item total
            item_total = item["amount"] * item["unit_price"]
            total += item_total
            
            # Print item details
            pdf.cell(col_widths[0], 7, item["description"], 1, 0, fill=fill)
            pdf.cell(col_widths[1], 7, str(item["amount"]), 1, 0, 'C', fill=fill)
            
            # Utiliser notre fonction personnalisée pour les prix
            pdf.set_x(pdf.get_x())
            draw_price_cell(col_widths[2], 7, item["unit_price"], 1, 0, 'R', fill)
            draw_price_cell(col_widths[3], 7, item_total, 1, 1, 'R', fill)

        # Totals section with variable position and formatting
        pdf.ln(5)
        
        # Variable position for totals
        totals_x = pdf.w - 90 if random.random() < 0.7 else pdf.get_x()
        
        # Conditionally show different tax fields
        show_ht = random.random() < 0.9  # 90% de chance de montrer le total HT
        show_tva = random.random() < 0.8  # 80% de chance de montrer la TVA
        
        # Ensure at least one is shown
        if not (show_ht or show_tva):
            show_ht = True
        
        # Format for totals
        pdf.set_font(font, '', text_size)
        if show_ht:
            pdf.set_x(totals_x)
            pdf.cell(50, 7, "Total HT:", 0, 0)
            pdf.set_x(totals_x + 50)
            draw_price_cell(40, 7, total, 0, 1, 'R')
        
        # Variable TVA rate
        tva_rate = random.choice(VAT_RATES)
        tva_amount = total * (tva_rate / 100)
        
        if show_tva:
            pdf.set_x(totals_x)
            pdf.cell(50, 7, f"TVA ({tva_rate:.1f}%):", 0, 0)
            pdf.set_x(totals_x + 50)
            draw_price_cell(40, 7, tva_amount, 0, 1, 'R')
        
        # Always show total TTC with emphasis
        pdf.set_x(totals_x)
        pdf.set_font(font, 'B', text_size)
        pdf.cell(50, 7, "Total TTC:", 0, 0)
        pdf.set_x(totals_x + 50)
        draw_price_cell(40, 7, total + tva_amount, 0, 1, 'R')
        
        # Add legal mentions at variable positions
        if random.random() < 0.7:
            pdf.ln(10)
            pdf.set_font(font, 'I', text_size - 2)
            
            mentions = [
                f"SIRET: {random.randint(10000000000000, 99999999999999)}",
                f"TVA Intracommunautaire: FR{random.randint(10000000, 99999999)}",
                "Payable sous 30 jours",
                "En cas de retard de paiement, une pénalité de 3% sera appliquée"
            ]
            
            # Show random subset of mentions
            for mention in random.sample(mentions, k=random.randint(1, len(mentions))):
                pdf.cell(0, 5, mention, ln=True)

        # Output PDF
        pdf.output(output_path)
        return output_path


def convert_pdf_to_image(pdf_path, output_path, image_effects=None):
    """Convert a PDF to an image and optionally apply effects"""
    from pdf2image import convert_from_path
    
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
    
    # If we have image effects to apply
    if image_effects:
        # Appliquer une texture de papier (NOUVEAU)
        if random.random() < 0.4:  # 40% chance to apply texture
            img = image_effects.apply_texture(img)
        
        # Apply defects if requested
        if random.random() < 0.5:
            img = image_effects.apply_defects(img)
        
        # Add handwriting if requested
        if random.random() < 0.3:
            img = image_effects.add_handwriting(img)
        
        # Add noise if requested
        if random.random() < 0.5:
            img = image_effects.add_noise(img)
    
    # Make sure the image is in RGB mode before saving as JPEG
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Save the enhanced image
    img.save(output_path)
    return output_path