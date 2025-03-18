from faker import Faker
from fpdf import FPDF
import random
from datetime import datetime, timedelta
import os

# Initialiser Faker en français
fake = Faker(['fr_FR'])

class InvoiceGenerator:
    def __init__(self):
        self.company_names = [
            "Tech Solutions SARL", "InfoSys France", "Digital Services SA",
            "Consulting Pro EURL", "Web Expert SAS"
        ]
        
    def generate_invoice_number(self):
        return f"FACT-{fake.random_number(digits=6)}"
    
    def generate_items(self):
        items = []
        services = [
            "Développement web", "Maintenance", "Formation",
            "Consultation", "Support technique", "Hébergement",
            "Design UX/UI", "SEO", "Développement mobile"
        ]
        
        for _ in range(random.randint(1, 5)):
            service = random.choice(services)
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(100, 1000), 2)
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
        # Utiliser les polices par défaut qui supportent l'Unicode
        pdf.set_font("Helvetica", size=12)
        
        # Remplacer toutes les instances de police dans le code
        # Arial -> Helvetica
        pdf.set_font("Helvetica", "B", 16)  # Pour le titre
        pdf.set_font("Helvetica", size=12)  # Pour le texte normal
        
        # En-tête de la facture
        company = random.choice(self.company_names)
        invoice_number = self.generate_invoice_number()
        date = fake.date_between(start_date='-1y', end_date='today')
        
        # Informations de l'entreprise
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, company, ln=True)
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, f"{fake.street_address()}", ln=True)
        pdf.cell(0, 10, f"{fake.postcode()} {fake.city()}", ln=True)
        pdf.cell(0, 10, f"Tél: {fake.phone_number()}", ln=True)
        pdf.cell(0, 10, f"Email: {fake.email()}", ln=True)
        
        # Numéro de facture et date
        pdf.ln(10)
        pdf.cell(0, 10, f"Facture N°: {invoice_number}", ln=True)
        pdf.cell(0, 10, f"Date: {date.strftime('%d/%m/%Y')}", ln=True)
        
        # Informations du client
        pdf.ln(10)
        pdf.cell(0, 10, "Facturé à:", ln=True)
        pdf.cell(0, 10, fake.company(), ln=True)
        pdf.cell(0, 10, fake.street_address(), ln=True)
        pdf.cell(0, 10, f"{fake.postcode()} {fake.city()}", ln=True)
        
        # Tableau des articles
        pdf.ln(10)
        items = self.generate_items()
        
        # En-têtes du tableau
        headers = ["Description", "Quantité", "Prix unitaire", "Total"]
        col_widths = [80, 30, 40, 40]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Contenu du tableau
        total_amount = 0
        for item in items:
            pdf.cell(col_widths[0], 10, item["description"], 1)
            pdf.cell(col_widths[1], 10, str(item["quantity"]), 1)
            pdf.cell(col_widths[2], 10, f"{item['unit_price']:.2f} EUR", 1)
            pdf.cell(col_widths[3], 10, f"{item['total']:.2f} EUR", 1)
            pdf.ln()
            total_amount += item["total"]
        
        # Total avec variation aléatoire des champs affichés
        pdf.ln(10)
        
        # Choisir aléatoirement quels totaux afficher
        show_ht = random.choice([True, True, True])  # 75% de chance d'afficher HT
        show_tva = random.choice([True, True, False])  # 66% de chance d'afficher TVA
        show_ttc = random.choice([True, True, True])  # 75% de chance d'afficher TTC
        
        # S'assurer qu'au moins un total est affiché
        if not any([show_ht, show_tva, show_ttc]):
            show_ttc = True
        
        # Afficher les totaux sélectionnés
        if show_ht:
            pdf.cell(0, 10, f"Total HT: {total_amount:.2f} EUR", ln=True)
        
        # Varier le taux de TVA (19.6%, 20%, 5.5%)
        tva_rate = random.choice([19.6, 20.0, 5.5])
        tva_amount = total_amount * (tva_rate / 100)
        
        if show_tva:
            pdf.cell(0, 10, f"TVA ({tva_rate}%): {tva_amount:.2f} EUR", ln=True)
        
        if show_ttc:
            total_ttc = total_amount + tva_amount
            pdf.cell(0, 10, f"Total TTC: {total_ttc:.2f} EUR", ln=True)
        
        # Sauvegarde du PDF
        pdf.output(output_path)

def generate_multiple_invoices(num_invoices, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    generator = InvoiceGenerator()
    
    for i in range(num_invoices):
        output_path = os.path.join(output_dir, f"facture_{i+1}.pdf")
        generator.create_pdf(output_path)
        print(f"Facture {i+1} générée: {output_path}")

if __name__ == "__main__":
    # Générer 20 factures dans le dossier "factures"
    generate_multiple_invoices(20, "factures") 