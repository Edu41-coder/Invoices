from fpdf import FPDF, XPos, YPos
import os
import random
from datetime import datetime, timedelta
from invoice_generator.config import FONTS, OUTPUT_DIRS
from invoice_generator.data_provider import fake
from invoice_generator.pdf_utils import convert_pdf_to_image

class DocumentGenerator:
    """Base class for generating non-invoice documents"""
    
    def __init__(self, data_provider=None, image_effects=None):
        self.data_provider = data_provider
        self.image_effects = image_effects
        self.temp_dir = OUTPUT_DIRS["temp"]
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def generate_document(self, output_path):
        """Should be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_document")
    
    def _create_pdf_and_convert(self, pdf_create_func, output_path, apply_defects=False, add_handwriting=False):
        """Helper to create a PDF and convert to image"""
        # Create a temporary PDF
        temp_pdf = os.path.join(self.temp_dir, f"temp_{random.randint(10000, 99999)}.pdf")
        
        # Generate the PDF
        pdf_create_func(temp_pdf)
        
        # Convert to image with effects
        convert_pdf_to_image(
            temp_pdf, 
            output_path,
            self.image_effects if (apply_defects or add_handwriting) else None
        )
        
        # Remove temp file
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
        
        return output_path


class LetterGenerator (DocumentGenerator):
    """Generates business letters"""
    
    def generate_document(self, output_path, apply_defects=True, add_handwriting=True):
        """Generate a business letter"""
        return self._create_pdf_and_convert(
            self._create_letter_pdf, 
            output_path,
            apply_defects,
            add_handwriting
        )
    
    def _create_letter_pdf(self, pdf_path):
        """Create a PDF business letter"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(["Helvetica", "Times", "Courier"])  # Toutes supportent les caractères français
        pdf.set_font(font, '', 12)
        
        # Sender info
        if self.data_provider:
            company = random.choice(self.data_provider.company_names)
        else:
            company = fake.company()
            
        pdf.cell(0, 10, company, ln=1)
        pdf.set_font(font, '', 10)
        pdf.cell(0, 5, fake.address().replace('\n', ', '), ln=1)
        pdf.cell(0, 5, fake.phone_number(), ln=1)
        
        # Date
        pdf.ln(10)
        date = datetime.now().strftime("%d %B %Y")
        pdf.cell(0, 5, date, ln=1, align='R')
        
        # Recipient
        pdf.ln(10)
        pdf.cell(0, 5, fake.name(), ln=1)
        pdf.cell(0, 5, fake.job(), ln=1)
        pdf.cell(0, 5, fake.company(), ln=1)
        pdf.multi_cell(0, 5, fake.address().replace('\n', ', '))
        
        # Subject
        pdf.ln(10)
        pdf.set_font(font, 'B', 11)
        pdf.cell(0, 8, f"Objet: {random.choice(['Demande de renseignements', 'Suivi de projet', 'Invitation', 'Confirmation de rendez-vous'])}", ln=1)
        
        # Content
        pdf.ln(5)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=5))
        pdf.ln(5)
        
        # Ajouter occasionnellement des références à des montants (40% de chance)
        if random.random() < 0.4:
            # Choisir entre € et EUR pour simuler des factures
            currency = "EUR"  # Par défaut pour éviter les problèmes de caractères
            
            # Créer un paragraphe avec mention financière
            money_text = random.choice([
                f"Comme convenu, notre budget alloué est de {random.randint(1000, 50000):.2f} {currency}.",
                f"Le montant total pour cette prestation s'élève à {random.randint(500, 10000):.2f} {currency}.",
                f"Nous vous confirmons la réception de votre paiement de {random.randint(100, 2000):.2f} {currency}.",
                f"Le devis estimé pour ce projet est de {random.randint(5000, 100000):.2f} {currency}."
            ])
            
            pdf.multi_cell(0, 6, money_text)
            pdf.ln(5)
        
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # Closing
        pdf.ln(10)
        pdf.cell(0, 5, "Cordialement,", ln=1)
        pdf.ln(10)
        pdf.cell(0, 5, fake.name(), ln=1)
        pdf.cell(0, 5, fake.job(), ln=1)
        
        # Output PDF
        pdf.output(pdf_path)


class MemoGenerator(DocumentGenerator):
    """Generates internal memos"""
    
    def generate_document(self, output_path, apply_defects=True, add_handwriting=True):
        """Generate an internal memo"""
        return self._create_pdf_and_convert(
            self._create_memo_pdf, 
            output_path,
            apply_defects,
            add_handwriting
        )
    
    def _create_memo_pdf(self, pdf_path):
        """Create a PDF internal memo"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(["Helvetica", "Times", "Courier"])  # Toutes supportent les caractères français
        
        # Header
        pdf.set_font(font, 'B', 16)
        pdf.cell(0, 10, "NOTE DE SERVICE", ln=1, align='C')
        
        # Details in a box
        pdf.set_font(font, '', 11)
        pdf.set_fill_color(240, 240, 240)
        
        pdf.cell(40, 8, "Date:", 1, 0, align='L', fill=1)
        pdf.cell(0, 8, datetime.now().strftime("%d/%m/%Y"), 1, 1, align='L')
        
        pdf.cell(40, 8, "De:", 1, 0, align='L', fill=1)
        pdf.cell(0, 8, fake.name(), 1, 1, align='L')
        
        pdf.cell(40, 8, "À:", 1, 0, align='L', fill=1)
        pdf.cell(0, 8, random.choice(["Tous les employés", "Service comptabilité", "Équipe marketing", "Direction"]), 1, 1, align='L')
        
        pdf.cell(40, 8, "Objet:", 1, 0, align='L', fill=1)
        pdf.cell(0, 8, random.choice(["Réunion mensuelle", "Procédures de sécurité", "Nouveaux horaires", "Événement d'entreprise"]), 1, 1, align='L')
        
        # Content
        pdf.ln(10)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=4))
        pdf.ln(5)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # Ajouter occasionnellement un tableau financier
        if random.random() < 0.3:
            pdf.ln(8)
            pdf.set_font(font, 'B', 12)
            pdf.cell(0, 8, "Budget prévisionnel:", ln=1)
            pdf.set_font(font, '', 11)
            
            # Entêtes du tableau
            pdf.set_fill_color(240, 240, 240)
            col_widths = [60, 40, 40, 40]
            headers = ["Département", "Budget", "Dépenses", "Solde"]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
            pdf.ln()
            
            # Contenu du tableau avec montants
            departments = ["Marketing", "R&D", "Administration", "Ventes"]
            currency = "EUR"  # Pour éviter les problèmes avec le symbole €
            
            for dept in departments:
                budget = random.randint(10000, 100000)
                expenses = random.randint(5000, budget)
                balance = budget - expenses
                
                pdf.cell(col_widths[0], 7, dept, 1, 0)
                pdf.cell(col_widths[1], 7, f"{budget:.2f} {currency}", 1, 0, 'R')
                pdf.cell(col_widths[2], 7, f"{expenses:.2f} {currency}", 1, 0, 'R')
                pdf.cell(col_widths[3], 7, f"{balance:.2f} {currency}", 1, 1, 'R')
        
        # List of items if applicable
        if random.random() < 0.5:
            pdf.ln(5)
            for i in range(random.randint(3, 5)):
                pdf.set_x(10)  # Réinitialiser la position X à une marge
                pdf.cell(8, 6, "-", 0, 0)  # Utiliser un tiret au lieu du bullet point
                pdf.multi_cell(0, 6, fake.sentence(nb_words=10))  # Limiter le nombre de mots
        
        # Signature
        pdf.ln(15)
        pdf.cell(0, 6, fake.name(), ln=1)
        pdf.cell(0, 6, fake.job(), ln=1)  # Remplacé job_title par job
        
        # Output PDF
        pdf.output(pdf_path)


class ReportGenerator(DocumentGenerator):
    """Generates business reports"""
    
    def generate_document(self, output_path, apply_defects=True, add_handwriting=True):
        """Generate a business report"""
        return self._create_pdf_and_convert(
            self._create_report_pdf, 
            output_path,
            apply_defects,
            add_handwriting
        )
    
    def _create_report_pdf(self, pdf_path):
        """Create a PDF business report"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(["Helvetica", "Times", "Courier"])  # Toutes supportent les caractères français
        
        # Title
        pdf.set_font(font, 'B', 16)
        report_type = random.choice(["RAPPORT D'ACTIVITÉ", "ANALYSE COMMERCIALE", "ÉTUDE DE MARCHÉ", "BILAN FINANCIER"])
        pdf.cell(0, 10, report_type, ln=1, align='C')
        
        # Period
        pdf.set_font(font, 'I', 12)
        month = random.choice(["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
        year = random.randint(2020, 2024)
        pdf.cell(0, 8, f"{month} {year}", ln=1, align='C')
        
        # Executive summary
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 8, "Résumé exécutif", ln=1)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=4))
        
        # Main sections
        sections = ["Résultats", "Analyse", "Perspectives"]
        
        for section in sections:
            pdf.ln(10)
            pdf.set_font(font, 'B', 14)
            pdf.cell(0, 8, section, ln=1)
            pdf.set_font(font, '', 11)
            pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=random.randint(3, 5)))
            
            # Ajouter un tableau financier dans la section Résultats ou Analyse
            if section in ["Résultats", "Analyse"] and random.random() < 0.6:
                pdf.ln(5)
                pdf.set_font(font, 'B', 12)
                pdf.cell(0, 8, "Données financières:", ln=1)
                
                # Tableau financier simple
                currency = "EUR"  # Plus sûr que le symbole €
                headers = ["Trimestre", "Revenus", "Dépenses", "Résultat"]
                col_width = pdf.w / 4.5
                
                # Entêtes
                pdf.set_fill_color(240, 240, 240)
                for header in headers:
                    pdf.cell(col_width, 8, header, 1, 0, 'C', True)
                pdf.ln()
                
                # Données financières trimestrielles
                for i in range(1, 5):
                    revenue = random.randint(100000, 500000)
                    expenses = random.randint(80000, revenue)
                    result = revenue - expenses
                    
                    pdf.cell(col_width, 7, f"T{i}", 1, 0, 'C')
                    pdf.cell(col_width, 7, f"{revenue:.2f} {currency}", 1, 0, 'R')
                    pdf.cell(col_width, 7, f"{expenses:.2f} {currency}", 1, 0, 'R')
                    pdf.cell(col_width, 7, f"{result:.2f} {currency}", 1, 1, 'R')
                
                # Totaux
                total_revenue = random.randint(500000, 1500000)
                total_expenses = random.randint(400000, total_revenue)
                total_result = total_revenue - total_expenses
                
                pdf.set_font(font, 'B', 11)
                pdf.cell(col_width, 7, "Total", 1, 0, 'C')
                pdf.cell(col_width, 7, f"{total_revenue:.2f} {currency}", 1, 0, 'R')
                pdf.cell(col_width, 7, f"{total_expenses:.2f} {currency}", 1, 0, 'R')
                pdf.cell(col_width, 7, f"{total_result:.2f} {currency}", 1, 1, 'R')
                
                pdf.set_font(font, '', 11)
            
            # Add some bullet points
            if random.random() < 0.7:
                pdf.ln(5)
                for i in range(random.randint(2, 4)):
                    pdf.set_x(10)  # Réinitialiser la position X à une marge
                    # Varier le style des puces pour plus de diversité
                    bullet = random.choice(["-", "*", ">", "o"])
                    pdf.cell(8, 6, bullet, 0, 0)  # Utiliser des caractères supportés par Latin-1
                    pdf.multi_cell(0, 6, fake.sentence(nb_words=10))  # Limiter le nombre de mots
        
        # Conclusion
        pdf.ln(10)
        pdf.set_font(font, 'B', 14)
        pdf.cell(0, 8, "Conclusion", ln=1)
        pdf.set_font(font, '', 11)
        pdf.multi_cell(0, 6, fake.paragraph(nb_sentences=3))
        
        # Output PDF
        pdf.output(pdf_path)


class FormGenerator(DocumentGenerator):
    """Generates business forms"""
    
    def generate_document(self, output_path, apply_defects=True, add_handwriting=True):
        """Generate a business form"""
        return self._create_pdf_and_convert(
            self._create_form_pdf, 
            output_path,
            apply_defects,
            add_handwriting
        )
    
    def _create_form_pdf(self, pdf_path):
        """Create a PDF form"""
        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Choose random font
        font = random.choice(["Helvetica", "Times", "Courier"])  # Toutes supportent les caractères français
        
        # Form title
        pdf.set_font(font, 'B', 16)
        form_type = random.choice(["FORMULAIRE D'INSCRIPTION", "DEMANDE DE CONGÉS", "BON DE COMMANDE", "FICHE DE RENSEIGNEMENTS"])
        pdf.cell(0, 10, form_type, ln=1, align='C')
        
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
                ("Prix unitaire:", f"{random.uniform(10, 500):.2f} EUR"),
                ("Prix total:", f"{random.uniform(500, 5000):.2f} EUR"),
                ("Date de livraison souhaitée:", (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%d/%m/%Y"))
            ])
        elif random.random() < 0.3:  # Ajouter des montants à d'autres formulaires parfois
            price_field = random.choice([
                ("Montant estimé:", f"{random.uniform(100, 10000):.2f} EUR"),
                ("Budget alloué:", f"{random.uniform(1000, 50000)::.2f} EUR"),
                ("Coût total:", f"{random.uniform(500, 20000):.2f} EUR"),
                ("Prix de référence:", f"{random.uniform(50, 2000):.2f} EUR")
            ])
            fields.append(price_field)
        
        # Draw form fields
        pdf.set_fill_color(240, 240, 240)
        for label, value in fields:
            pdf.set_font(font, 'B', 11)
            pdf.cell(50, 8, label, 0, 0)
            pdf.set_font(font, '', 11)
            
            # Either pre-filled or empty
            if random.random() < 0.4:
                pdf.cell(0, 8, value, 0, 1)
            else:
                pdf.cell(0, 8, "________________", 0, 1)
        
        # Signature area
        pdf.ln(15)
        pdf.cell(0, 8, "Date: ________________", 0, 1)
        pdf.cell(0, 8, "Signature:", 0, 1)
        pdf.cell(80, 20, "", 1)
        
        # Output PDF
        pdf.output(pdf_path)