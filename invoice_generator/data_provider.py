from faker import Faker

# Initialize Faker in French
fake = Faker(['fr_FR'])

class DataProvider:
    def __init__(self):
        # DIY Companies
        self.diy_companies = [
            "LEROY MERLIN", "CASTORAMA", "BRICORAMA", "BRICO DÉPÔT",
            "BRICOMARCHÉ", "MR BRICOLAGE", "WELDOM", "BRICOMAN"
        ]
        
        # Tech Companies
        self.tech_companies = [
            "Tech Solutions SARL", "InfoSys France", "Digital Services SA",
            "Consulting Pro EURL", "Web Expert SAS", "Data Analytics SARL",
            "Cloud Systems SAS", "Smart IT Services"
        ]
        
        # Retail Companies
        self.retail_companies = [
            "CARREFOUR", "AUCHAN", "E.LECLERC", "INTERMARCHÉ",
            "SUPER U", "LIDL FRANCE", "CASINO", "MONOPRIX"
        ]
        
        # Insurance Companies
        self.insurance_companies = [
            "AXA France", "MAIF Assurances", "MATMUT", "Groupama",
            "Allianz France", "MMA Assurances", "Generali France", "AG2R La Mondiale"
        ]
        
        # Telecom Companies
        self.telecom_companies = [
            "ORANGE", "SFR", "BOUYGUES TELECOM", "FREE MOBILE",
            "SOSH", "RED by SFR", "B&YOU", "NRJ Mobile"
        ]
        
        # Healthcare Companies
        self.healthcare_companies = [
            "Laboratoire Médical Central", "Centre Médical St-Jacques", "Pharmacie de la Gare", 
            "Clinique Médicale Express", "Analyse Biomédicale SARL", "Institut Paramédical",
            "Pharmacie du Boulevard", "Centre Optique Vision Plus"
        ]
        
        # All companies
        self.company_names = (self.diy_companies + self.tech_companies + 
                             self.retail_companies + self.insurance_companies + 
                             self.telecom_companies + self.healthcare_companies)
        
        # Company styles
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
        
        # Items by sector
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

    def get_items_for_company_type(self, company_type):
        """Returns appropriate items based on company type"""
        if company_type == 'diy':
            return self.diy_companies, self.diy_items
        elif company_type == 'tech':
            return self.tech_companies, self.tech_items
        elif company_type == 'retail':
            return self.retail_companies, self.retail_items
        elif company_type == 'insurance':
            return self.insurance_companies, self.insurance_items
        elif company_type == 'telecom':
            return self.telecom_companies, self.telecom_items
        else:  # healthcare
            return self.healthcare_companies, self.healthcare_items

    def get_fallback_company_name(self):
        """Return a fallback company name in case no specific ones are available"""
        return f"{fake.company()} {fake.company_suffix()}"