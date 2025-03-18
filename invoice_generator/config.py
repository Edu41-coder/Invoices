import os

# Output directory structure
OUTPUT_BASE = "dataset"
OUTPUT_DIRS = {
    "original": os.path.join(OUTPUT_BASE, "original"),
    "training_invoices": os.path.join(OUTPUT_BASE, "training", "invoices"),
    "training_non_invoices": os.path.join(OUTPUT_BASE, "training", "non_invoices"),
    "validation_invoices": os.path.join(OUTPUT_BASE, "validation", "invoices"),
    "validation_non_invoices": os.path.join(OUTPUT_BASE, "validation", "non_invoices"),
    "test_invoices": os.path.join(OUTPUT_BASE, "test", "invoices"),
    "test_non_invoices": os.path.join(OUTPUT_BASE, "test", "non_invoices"),
    "sample": os.path.join(OUTPUT_BASE, "sample"),
    "temp": os.path.join(OUTPUT_BASE, "temp"),
}

# Assets paths
ASSETS_DIR = "assets"
COFFEE_STAINS_DIR = os.path.join(ASSETS_DIR, "coffee_stains")
FOLDS_DIR = os.path.join(ASSETS_DIR, "folds")
HANDWRITING_DIR = os.path.join(ASSETS_DIR, "handwriting")
STAMPS_DIR = os.path.join(ASSETS_DIR, "stamps")
TEXTURES_DIR = os.path.join(ASSETS_DIR, "textures")  # Ajout du répertoire textures

# Default fonts and layouts
FONTS = ["Helvetica", "Times", "Courier"]

# Ajouter ces définitions après FONTS et avant LAYOUTS
COLORS = {
    "black": (0, 0, 0),
    "dark_blue": (0, 0, 139),
    "dark_green": (0, 100, 0),
    "dark_grey": (69, 69, 69),
    "purple": (128, 0, 128),
    "burgundy": (128, 0, 32)
}

# Enrichir les layouts existants
LAYOUTS = ["standard", "modern", "compact", "detailed", "minimal", "premium", "classic"]

# Ajouter les formats d'identifiants de facture
INVOICE_ID_FORMATS = [
    "INV-{year}-{number}",
    "FACT-{number}",
    "FA/{year}/{number}",
    "F{year}{number}",
    "{number}/INV/{year}"
]

# Taux de TVA possibles en France
VAT_RATES = [20.0, 10.0, 5.5, 2.1]

# Dataset generation defaults
DEFAULT_SPLIT = (0.7, 0.15, 0.15)  # Train, Val, Test