import os
import torch
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
from transformers import (
    LayoutLMForSequenceClassification, 
    LayoutLMForTokenClassification,
    LayoutLMTokenizer,
    AdamW
)
from torch.utils.data import Dataset, DataLoader
import sqlite3
from pathlib import Path
import mysql.connector
from datetime import datetime
from pdf2image import convert_from_path
import tempfile
import os
from tqdm import tqdm
import time

# Define entity labels for NER
ENTITY_LABELS = [
    "O",               # Outside of any entity
    "B-TotalHT",       # Beginning of Total HT
    "I-TotalHT",       # Inside of Total HT
    "B-TotalTTC",      # Beginning of Total TTC
    "I-TotalTTC",      # Inside of Total TTC
    "B-TVA",           # Beginning of TVA
    "I-TVA",           # Inside of TVA
    "B-ClientName",    # Beginning of Client Name
    "I-ClientName",    # Inside of Client Name
    "B-ClientAddress", # Beginning of Client Address (nouveau) (nouveau)
    "I-ClientAddress", # Inside of Client Address (nouveau) (nouveau)
    "B-InvoiceNum",    # Beginning of Invoice Number
    "I-InvoiceNum",    # Inside of Invoice Number
    "B-Date",          # Beginning of Date
    "I-Date",          # Inside of Date
    "B-CompanyName",   # Beginning of Company Name
    "I-CompanyName",   # Inside of Company Name  
    "B-TVANumber",     # Beginning of TVA Number (nouveau)
    "I-TVANumber"      # Inside of TVA Number (nouveau)
]

class InvoiceProcessor:
    def __init__(self, ocr_engine="tesseract"):
        """Initialize the invoice processor"""
        self.tokenizer = LayoutLMTokenizer.from_pretrained("microsoft/layoutlm-base-uncased")
        self.ocr_engine = ocr_engine
        
    def process_document(self, document_path, image=None):
        """Process a document image or PDF to extract text and layout information"""
        if image is None:
            if document_path.lower().endswith('.pdf'):
                # Convert PDF to image
                with tempfile.TemporaryDirectory() as path:
                    images = convert_from_path(document_path, output_folder=path)
                    if not images:
                        raise ValueError(f"Unable to convert PDF to image: {document_path}")
                    # Use the first page for processing
                    image = images[0]
            else:
                # Load image directly
                image = Image.open(document_path).convert("RGB")
        
        # Extract text and bounding boxes using OCR
        ocr_results = self._perform_ocr(image)
        
        # Convert OCR results to LayoutLM input format
        words, boxes, word_labels = self._prepare_layoutlm_input(ocr_results)
        
        # Tokenize and create model inputs
        inputs = self._tokenize(words, boxes)
        
        return {
            "image_path": document_path,
            "words": words,
            "boxes": boxes,
            "inputs": inputs,
            "raw_image": image
        }
    
    def _perform_ocr(self, image):
        """Perform OCR on the image"""
        # Extract text and bounding boxes using pytesseract
        ocr_df = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
        
        # Filter out empty text
        ocr_df = ocr_df[ocr_df.text.notnull()]
        
        # Normalize bounding boxes to match LayoutLM requirements
        width, height = image.size
        
        results = []
        for _, row in ocr_df.iterrows():
            if pd.notna(row['text']) and str(row['text']).strip():
                # Get coordinates and normalize
                x1 = int(row['left']) / width * 1000
                y1 = int(row['top']) / height * 1000
                x2 = min((int(row['left']) + int(row['width'])) / width * 1000, 1000)
                y2 = min((int(row['top']) + int(row['height'])) / height * 1000, 1000)
                
                # Ensure coordinates are valid
                x1, y1, x2, y2 = max(0, x1), max(0, y1), max(0, x2), max(0, y2)
                
                results.append({
                    "text": str(row['text']).strip(),
                    "box": [int(x1), int(y1), int(x2), int(y2)]  # Correction: ajout d'une virgule ici
                })
        
        return results
    
    def _prepare_layoutlm_input(self, ocr_results):
        """Convert OCR results to LayoutLM input format"""
        words = []
        boxes = []
        word_labels = []
        
        for item in ocr_results:
            words.append(item["text"])
            # Assurez-vous que toutes les coordonnées sont des entiers et dans les limites
            box = [max(0, min(int(coord), 1000)) for coord in item["box"]]
            boxes.append(box)
            word_labels.append("O")
            
        return words, boxes, word_labels
    
    def _tokenize(self, words, boxes):
        """Tokenize the text with layout information"""
        # Combine all words into a text
        text = " ".join(words)
        
        # LayoutLM expects a specific format for boxes
        word_boxes = []
        token_boxes = []
        
        for i, box in enumerate(boxes):
            # Each word may be tokenized into multiple tokens
            word_tokens = self.tokenizer.tokenize(words[i])
            token_boxes.extend([box] * len(word_tokens))
        
        # Add special tokens and their boxes
        encoding = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Add layout information
        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]
        token_type_ids = encoding["token_type_ids"]
        
        # Pad the boxes to match the tokens
        padded_boxes = self._pad_boxes(token_boxes, encoding)
        
        # CORRECTION: S'assurer que le tenseur bbox a la forme attendue (batch, seq_length, 4)
        bbox_tensor = torch.tensor(padded_boxes, dtype=torch.long)
        
        # Vérifier et corriger les dimensions
        if len(bbox_tensor.shape) == 2:  # Si (seq_length, 4)
            bbox_tensor = bbox_tensor.unsqueeze(0)  # Ajouter dimension batch
        elif len(bbox_tensor.shape) > 3:  # Si trop de dimensions
            bbox_tensor = bbox_tensor.view(input_ids.shape[0], input_ids.shape[1], 4)
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
            "bbox": bbox_tensor
        }
    
    def _pad_boxes(self, token_boxes, encoding):
        """Pad the boxes to match the tokenized input"""
        # Number of tokens after tokenization with special tokens
        seq_length = encoding["input_ids"].shape[1]
        
        # Initialize box for CLS token as [0, 0, 0, 0]
        padded_boxes = [[0, 0, 0, 0]]
        
        # Add actual token boxes
        padded_boxes.extend(token_boxes)
        
        # Add box for SEP token as [1000, 1000, 1000, 1000]
        padded_boxes.append([1000, 1000, 1000, 1000])
        
        # Pad with [0, 0, 0, 0] boxes
        while len(padded_boxes) < seq_length:
            padded_boxes.append([0, 0, 0, 0])
        
        # Truncate if needed
        padded_boxes = padded_boxes[:seq_length]
        
        return padded_boxes
    
    def _normalize_tensor_dimensions(self, tensor):
        """Normalise les dimensions du tenseur pour LayoutLM"""
        if tensor is None:
            return None
        
        # Si tenseur à 5 dimensions (problème actuel), supprimer la dimension excessive
        if len(tensor.shape) == 5:
            return tensor.squeeze(1)
        
        return tensor

    # Modifier cette fonction:
    def standardize_bbox_format(self, bbox):
        """S'assurer que les coordonnées de boîtes sont au bon format"""
        if bbox is None:
            return None
        
        # Modifier pour garantir que les coordonnées sont au format attendu
        if len(bbox.shape) == 4 and bbox.shape[1] == 1:  # [batch, 1, seq, 4]
            # Supprimer la dimension 1
            bbox = bbox.squeeze(1)
        
        # S'assurer que la dernière dimension est bien 4 (x1, y1, x2, y2)
        if bbox.shape[-1] != 4:
            raise ValueError(f"Format de bbox incorrect: {bbox.shape}, doit se terminer par 4")
        
        return bbox


class InvoiceDataset(Dataset):
    def __init__(self, data_dir, processor, is_classification=True, negative_dirs=None):
        self.data_dir = Path(data_dir)
        self.processor = processor
        self.is_classification = is_classification
        self.negative_dirs = [Path(d) for d in negative_dirs] if negative_dirs else None
        
        # Trouver tous les fichiers images
        self.image_paths = list(self.data_dir.glob('**/*.jpg')) + list(self.data_dir.glob('**/*.jpeg'))
        self.image_paths += list(self.data_dir.glob('**/*.png'))
        
        # Ajouter ces logs de débogage
        print(f"\nRecherche d'images dans: {self.data_dir}")
        print(f"Images trouvées: {len(self.image_paths)}")
        if len(self.image_paths) == 0:
            print("ATTENTION: Aucune image trouvée!")
            all_files = list(self.data_dir.glob('**/*.*'))
            print(f"Fichiers présents (toutes extensions): {len(all_files)}")
            if all_files:
                extensions = set([p.suffix for p in all_files])
                print(f"Extensions trouvées: {extensions}")
        
        # Determine labels based on path
        self.labels = []
        for path in self.image_paths:
            # Check if path is in one of the negative_dirs
            is_negative = False
            path_str = str(path).lower()
            
            if negative_dirs:
                for neg_dir in negative_dirs:
                    neg_dir_lower = str(neg_dir).lower()
                    if neg_dir_lower in path_str:
                        is_negative = True
                        break
            
            # Also check if containing folder is named "non_invoices"
            if "non_invoices" in path_str or "non-invoices" in path_str:
                is_negative = True
                
            self.labels.append(0 if is_negative else 1)
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image_path = str(self.image_paths[idx])
        try:
            # Uniformiser la taille des images
            with Image.open(image_path) as img:
                # Redimensionner à une taille fixe pour éviter les problèmes
                img = img.resize((512, 512))
                # Continuer le traitement avec l'image redimensionnée
                processed = self.processor.process_document(image_path, image=img)
            
            if self.is_classification:
                # Pour classification de document
                return {
                    **processed["inputs"],
                    "labels": torch.tensor(self.labels[idx], dtype=torch.long)
                }
            else:
                # Pour NER
                seq_length = processed["inputs"]["input_ids"].shape[1]
                token_labels = torch.zeros(seq_length, dtype=torch.long)
                
                return {
                    **processed["inputs"],
                    "labels": token_labels
                }
        except Exception as e:
            print(f"Erreur lors du traitement de l'image {image_path}: {e}")
            # Fournir un élément valide en cas d'erreur
            if idx > 0:
                return self.__getitem__(idx-1)  # Essayer avec l'image précédente
            else:
                raise e  # Impossible de trouver une alternative


class InvoiceModel:
    # Ajouter ces constantes au début de la classe
    # Seuils de confiance pour chaque champ
    CONFIDENCE_THRESHOLDS = {
        "invoice_number": 0.7,
        "date": 0.6,
        "client_name": 0.7,
        "client_address": 0.5,
        "total_ht": 0.8,
        "tva": 0.8,
        "total_ttc": 0.8,
        "company_name": 0.7,
        "tva_number": 0.6
    }
    
    def __init__(self, model_dir="model_output"):
        """Initialize the invoice model"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize models
        self.classifier = LayoutLMForSequenceClassification.from_pretrained(
            "microsoft/layoutlm-base-uncased", 
            num_labels=2
        )
        
        self.ner_model = LayoutLMForTokenClassification.from_pretrained(
            "microsoft/layoutlm-base-uncased",
            num_labels=len(ENTITY_LABELS)
        )
        
        self.processor = InvoiceProcessor()
        
        # Database connection
        self.db_path = self.model_dir / "invoices.db"
        self.setup_database()
    
    def setup_database(self):
        """Set up the MySQL database connection"""
        # Configuration de la connexion MySQL
        self.db_config = {
            'user': 'root',
            'password': '',  # Par défaut vide dans XAMPP
            'host': 'localhost',
            'database': 'invoice_analyzer'
        }
        
        # Tester la connexion
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Vérifier si les tables existent déjà
            cursor.execute("SHOW TABLES LIKE 'invoices'")
            if not cursor.fetchone():
                # Créer la table invoices si elle n'existe pas
                cursor.execute('''
                CREATE TABLE invoices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file_path VARCHAR(255) NOT NULL,
                    is_invoice TINYINT(1) NOT NULL,
                    invoice_number VARCHAR(50),
                    date_invoice DATE,
                    client_name VARCHAR(100),
                    client_address VARCHAR(255),
                    total_ht DECIMAL(10,2),
                    tva DECIMAL(10,2),
                    total_ttc DECIMAL(10,2),
                    company_name VARCHAR(100),
                    tva_number VARCHAR(50),
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence_score DECIMAL(5,2)
                )
                ''')
                print("Table 'invoices' créée avec succès.")
            
            # Vérifier si la table extraction_logs existe
            cursor.execute("SHOW TABLES LIKE 'extraction_logs'")
            if not cursor.fetchone():
                # Créer la table extraction_logs si elle n'existe pas
                cursor.execute('''
                CREATE TABLE extraction_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    execution_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    file_processed VARCHAR(255),
                    processing_time_ms INT,
                    status VARCHAR(50),
                    error_message TEXT,
                    model_version VARCHAR(50)
                )
                ''')
                print("Table 'extraction_logs' créée avec succès.")
            
            # Création d'une nouvelle table pour les logs de confiance
            cursor.execute("SHOW TABLES LIKE 'field_confidence_logs'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE field_confidence_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    invoice_id INT NOT NULL,
                    field_name VARCHAR(50) NOT NULL,
                    raw_value TEXT,
                    confidence_score DECIMAL(5,2) NOT NULL,
                    is_uncertain BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
                ''')
                print("Table 'field_confidence_logs' créée avec succès.")
            
            conn.commit()
            print("Connexion à la base de données établie avec succès.")
        except mysql.connector.Error as err:
            print(f"Erreur de connexion à la base de données: {err}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    def train_classifier(self, train_dir, val_dir, epochs=3, batch_size=8, learning_rate=5e-5, negative_dir="dataset/non_invoices"):
        """Train the document classifier"""
        # Create datasets with positive and negative examples
        train_dataset = InvoiceDataset(train_dir, self.processor, is_classification=True, negative_dirs=[negative_dir])
        val_dataset = InvoiceDataset(val_dir, self.processor, is_classification=True, negative_dirs=[negative_dir])
        
        train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_dataloader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Ajouter au début de train_classifier pour déboguer
        for idx, batch in enumerate(train_dataloader):
            print(f"\nForme des tenseurs dans batch {idx}:")
            print(f"input_ids: {batch['input_ids'].shape}")
            print(f"attention_mask: {batch['attention_mask'].shape}")
            print(f"token_type_ids: {batch['token_type_ids'].shape}")
            print(f"bbox: {batch['bbox'].shape}")
            print(f"labels: {batch['labels'].shape}")
            
            if idx >= 2:  # Afficher les 3 premiers lots seulement
                break
        
        # Training setup
        optimizer = AdamW(self.classifier.parameters(), lr=learning_rate)
        
        # Ajouter cette fonction auxiliaire
        def fix_dimensions(batch):
            """Corriger les dimensions des tenseurs"""
            fixed_batch = {}
            for key, tensor in batch.items():
                if key in ["input_ids", "attention_mask", "token_type_ids"]:
                    if len(tensor.shape) == 3:  # Si forme [batch, 1, seq_len]
                        fixed_batch[key] = tensor.squeeze(1)  # Supprimer la dimension du milieu
                    else:
                        fixed_batch[key] = tensor
                elif key == "bbox":
                    if len(tensor.shape) == 4 and tensor.shape[1] == 1:  # Si forme [batch, 1, seq_len, 4]
                        fixed_batch[key] = tensor.squeeze(1)  # Supprimer la dimension excessive
                    else:
                        fixed_batch[key] = tensor
                else:
                    fixed_batch[key] = tensor
            return fixed_batch
        
        # Training loop
        self.classifier.train()
        for epoch in range(epochs):
            print(f"Starting epoch {epoch + 1}/{epochs}")
            epoch_start = time.time()
            batch_progress = tqdm(train_dataloader, desc=f"Epoch {epoch+1}", unit="batch")
            batch_count = 0
            
            for batch in batch_progress:
                batch_count += 1
                # Corriger les dimensions avant de déplacer vers le GPU
                batch = fix_dimensions(batch)
                
                # Move batch to GPU if available
                input_ids = batch["input_ids"].to(self.classifier.device)
                attention_mask = batch["attention_mask"].to(self.classifier.device)
                token_type_ids = batch["token_type_ids"].to(self.classifier.device)
                bbox = self.standardize_bbox_format(batch["bbox"]).to(self.classifier.device)
                labels = batch["labels"].to(self.classifier.device)
                
                # Forward pass
                outputs = self.classifier(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    token_type_ids=token_type_ids,
                    bbox=bbox,
                    labels=labels
                )
                
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
                
                # Mettre à jour la barre de progression
                batch_progress.set_postfix(loss=f"{loss.item():.4f}")
                
                # Afficher un log toutes les 5 images
                if batch_count % 5 == 0:
                    print(f"  • Traité {batch_count}/{len(train_dataloader)} batches, loss: {loss.item():.4f}")
            
            epoch_time = time.time() - epoch_start
            print(f"Epoch {epoch+1} terminée en {epoch_time:.2f} secondes")
            
            # Validation
            print("Validation...")
            self.classifier.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for batch in val_dataloader:
                    # Appliquer la même correction aux tenseurs de validation
                    batch = fix_dimensions(batch)
                    
                    input_ids = batch["input_ids"].to(self.classifier.device)
                    attention_mask = batch["attention_mask"].to(self.classifier.device)
                    token_type_ids = batch["token_type_ids"].to(self.classifier.device)
                    bbox = self.standardize_bbox_format(batch["bbox"]).to(self.classifier.device)
                    labels = batch["labels"].to(self.classifier.device)
                    
                    outputs = self.classifier(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        token_type_ids=token_type_ids,
                        bbox=bbox,
                        labels=labels
                    )
                    
                    val_loss += outputs.loss.item()
                    logits = outputs.logits
                    predictions = torch.argmax(logits, dim=-1)
                    val_correct += (predictions == labels).sum().item()
                    val_total += labels.size(0)
                    
                    
            
            accuracy = val_correct / val_total
            print(f"Epoch {epoch + 1} - Validation Loss: {val_loss / len(val_dataloader):.4f}, Accuracy: {accuracy:.4f}")
            
            # Save the model after each epoch
            self.classifier.save_pretrained(self.model_dir / f"classifier_epoch_{epoch + 1}")
            torch.save(self.classifier.state_dict(), f"{self.model_dir}/classifier_epoch_{epoch+1}.pt")
            print(f"Modèle sauvegardé: classifier_epoch_{epoch+1}.pt")
    
    def train_ner_model(self, train_dir, val_dir, epochs=3, batch_size=8, learning_rate=5e-5):
        """Train the NER model for field extraction"""
        # Create datasets
        train_dataset = InvoiceDataset(train_dir, self.processor, is_classification=False)
        val_dataset = InvoiceDataset(val_dir, self.processor, is_classification=False)
        
        train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_dataloader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Training setup
        optimizer = AdamW(self.ner_model.parameters(), lr=learning_rate)
        
        # Training loop
        self.ner_model.train()
        for epoch in range(epochs):
            print(f"Starting NER training epoch {epoch + 1}/{epochs}")
            total_loss = 0
            
            for batch in train_dataloader:
                # Move batch to GPU if available
                input_ids = batch["input_ids"].to(self.ner_model.device)
                attention_mask = batch["attention_mask"].to(self.ner_model.device)
                token_type_ids = batch["token_type_ids"].to(self.ner_model.device)
                bbox = batch["bbox"].to(self.ner_model.device)
                labels = batch["labels"].to(self.ner_model.device)
                
                # Forward pass
                outputs = self.ner_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    token_type_ids=token_type_ids,
                    bbox=bbox,
                    labels=labels
                )
                
                loss = outputs.loss
                total_loss += loss.item()
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
            
            print(f"Epoch {epoch + 1} - Average training loss: {total_loss / len(train_dataloader):.4f}")
            
            # Validation
            self.ner_model.eval()
            val_loss = 0
            
            with torch.no_grad():
                for batch in val_dataloader:
                    input_ids = batch["input_ids"].to(self.ner_model.device)
                    attention_mask = batch["attention_mask"].to(self.ner_model.device)
                    token_type_ids = batch["token_type_ids"].to(self.ner_model.device)
                    bbox = batch["bbox"].to(self.ner_model.device)
                    labels = batch["labels"].to(self.ner_model.device)
                    
                    outputs = self.ner_model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        token_type_ids=token_type_ids,
                        bbox=bbox,
                        labels=labels
                    )
                    
                    val_loss += outputs.loss.item()
            
            print(f"Epoch {epoch + 1} - Validation Loss: {val_loss / len(val_dataloader):.4f}")
            
            # Save the model after each epoch
            self.ner_model.save_pretrained(self.model_dir / f"ner_model_epoch_{epoch + 1}")
    
    def process_document(self, document_path):
        """Process a document for classification and field extraction"""
        # Process document
        processed = self.processor.process_document(document_path)
        
        # Classification
        inputs = {k: v.to(self.classifier.device) for k, v in processed["inputs"].items()}
        
        self.classifier.eval()
        with torch.no_grad():
            outputs = self.classifier(**inputs)
            logits = outputs.logits
            prediction = torch.argmax(logits, dim=-1).item()
        
        is_invoice = prediction == 1
        
        # If it's an invoice, extract fields
        extracted_fields = {}
        if (is_invoice):
            self.ner_model.eval()
            with torch.no_grad():
                ner_outputs = self.ner_model(**inputs)
                ner_predictions = torch.argmax(ner_outputs.logits, dim=-1)
            
            # Convert predictions to labels
            # This would need to be extended to actually extract the values
            extracted_fields = self._extract_fields_from_predictions(
                processed["words"], 
                processed["boxes"], 
                ner_predictions[0].cpu().numpy(),
                processed["raw_image"]
            )
            
            # Store in database
            self._store_in_database(document_path, is_invoice, extracted_fields)
        
        return {
            "is_invoice": is_invoice,
            "fields": extracted_fields
        }
    
    def _extract_fields_from_predictions(self, words, boxes, predictions, image):
        """Extract structured fields from NER predictions"""
        # Dictionary to store extracted fields
        extracted_fields = {
            "invoice_number": "",
            "date": "",
            "client_name": "",
            "client_address": "",
            "total_ht": 0.0,
            "tva": 0.0,
            "total_ttc": 0.0,
            "company_name": "",
            "tva_number": ""
        }
        
        # Map from label indices to label names
        idx_to_label = {i: label for i, label in enumerate(ENTITY_LABELS)}
        
        # Group words by entity
        entity_words = {}
        current_entity = "O"
        current_text = []
        
        for i, (word, pred_idx) in enumerate(zip(words, predictions)):
            pred_label = idx_to_label[pred_idx]
            
            # If we find a new entity
            if (pred_label.startswith("B-")):
                # Save previous entity if it exists
                if (current_entity != "O" and current_text):
                    entity_type = current_entity.replace("B-", "").replace("I-", "")
                    entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
                
                # Start new entity
                current_entity = pred_label
                current_text = [word]
            
            # If we're inside an entity
            elif (pred_label.startswith("I-") and current_entity != "O"):
                # If the I- tag matches the current entity
                if (pred_label.replace("I-", "B-") == current_entity):
                    current_text.append(word)
                else:
                    # Mismatch - save current entity and reset
                    entity_type = current_entity.replace("B-", "").replace("I-", "")
                    entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
                    current_entity = "O"
                    current_text = []
            
            # Outside any entity
            else:
                # Save previous entity if it exists
                if (current_entity != "O" and current_text):
                    entity_type = current_entity.replace("B-", "").replace("I-", "")
                    entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
                
                # Reset
                current_entity = "O"
                current_text = []
        
        # Don't forget the last entity
        if (current_entity != "O" and current_text):
            entity_type = current_entity.replace("B-", "").replace("I-", "")
            entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
        
        # Dictionnaire pour stocker les scores de confiance par champ
        confidence_scores = {}
        
        # 1. Numéro de facture
        if "InvoiceNum" in entity_words and entity_words["InvoiceNum"]:
            raw_value = entity_words["InvoiceNum"][0]
            # Score basé sur la longueur et le format (présence de chiffres)
            has_digits = any(c.isdigit() for c in raw_value)
            good_length = 3 <= len(raw_value) <= 20
            score = 0.5 + (0.25 if has_digits else 0) + (0.25 if good_length else 0)
            
            confidence_scores["invoice_number"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["invoice_number"]:
                extracted_fields["invoice_number"] = raw_value
                print(f"Champ extrait: invoice_number = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["invoice_number"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour invoice_number = '{raw_value}' (score: {score:.2f})")
        
        # 2. Date
        if "Date" in entity_words and entity_words["Date"]:
            raw_value = entity_words["Date"][0]
            # Score basé sur la validité du format date
            valid_date = self._validate_and_normalize_french_date(raw_value) is not None
            has_digits = any(c.isdigit() for c in raw_value)
            good_length = 6 <= len(raw_value) <= 12
            
            score = 0.3 + (0.4 if valid_date else 0) + (0.2 if has_digits else 0) + (0.1 if good_length else 0)
            confidence_scores["date"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["date"]:
                extracted_fields["date"] = raw_value
                print(f"Champ extrait: date = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["date"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour date = '{raw_value}' (score: {score:.2f})")
        
        # 3. Nom du client
        if "ClientName" in entity_words and entity_words["ClientName"]:
            raw_value = entity_words["ClientName"][0]
            # Score basé sur la longueur et la présence de lettres
            has_letters = any(c.isalpha() for c in raw_value)
            good_length = 3 <= len(raw_value) <= 100
            score = 0.4 + (0.3 if has_letters else 0) + (0.3 if good_length else 0)
            
            confidence_scores["client_name"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["client_name"]:
                extracted_fields["client_name"] = raw_value
                print(f"Champ extrait: client_name = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["client_name"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour client_name = '{raw_value}' (score: {score:.2f})")
        
        # 4. Adresse client
        if "ClientAddress" in entity_words and entity_words["ClientAddress"]:
            raw_value = entity_words["ClientAddress"][0]
            # Score basé sur la longueur et présence de valeurs attendues
            has_digits = any(c.isdigit() for c in raw_value)
            has_letters = any(c.isalpha() for c in raw_value)
            good_length = 10 <= len(raw_value) <= 200
            score = 0.2 + (0.2 if has_digits else 0) + (0.3 if has_letters else 0) + (0.3 if good_length else 0)
            
            confidence_scores["client_address"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["client_address"]:
                extracted_fields["client_address"] = raw_value
                print(f"Champ extrait: client_address = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["client_address"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour client_address = '{raw_value}' (score: {score:.2f})")
        
        # 5. Total HT
        if "TotalHT" in entity_words and entity_words["TotalHT"]:
            raw_value = entity_words["TotalHT"][0]
            try:
                # Nettoyer et extraire la valeur
                cleaned_value = raw_value.replace("€", "").replace("EUR", "").replace(",", ".")
                import re
                match = re.search(r'(\d+(\.\d+)?)', cleaned_value)
                if match:
                    numeric_value = float(match.group(1))
                    # Score basé sur la présence d'un montant valide
                    realistic_amount = 1.0 <= numeric_value <= 100000.0
                    score = 0.6 + (0.4 if realistic_amount else 0)
                    
                    confidence_scores["total_ht"] = score
                    
                    if score >= self.CONFIDENCE_THRESHOLDS["total_ht"]:
                        extracted_fields["total_ht"] = numeric_value
                        print(f"Champ extrait: total_ht = {numeric_value:.2f} (confiance: {score:.2f})")
                    else:
                        extracted_fields["total_ht"] = numeric_value
                        print(f"ATTENTION: Faible confiance pour total_ht = {numeric_value:.2f} (score: {score:.2f})")
                else:
                    confidence_scores["total_ht"] = 0.3
                    extracted_fields["total_ht"] = 0.0
                    print(f"ATTENTION: Format invalide pour total_ht: '{raw_value}' (score: 0.30)")
            except:
                confidence_scores["total_ht"] = 0.2
                extracted_fields["total_ht"] = 0.0
                print(f"ERREUR: Impossible d'extraire total_ht depuis '{raw_value}' (score: 0.20)")
        
        # 6. TVA
        if "TVA" in entity_words and entity_words["TVA"]:
            raw_value = entity_words["TVA"][0]
            try:
                # Nettoyer et extraire la valeur
                cleaned_value = raw_value.replace("€", "").replace("EUR", "").replace(",", ".")
                import re
                match = re.search(r'(\d+(\.\d+)?)', cleaned_value)
                if match:
                    numeric_value = float(match.group(1))
                    # Score basé sur la présence d'un montant valide de TVA
                    realistic_tva = 0.0 <= numeric_value <= 30000.0
                    standard_tva = numeric_value in [5.5, 10.0, 20.0] or abs(numeric_value - 5.5) < 0.1 or abs(numeric_value - 10.0) < 0.1 or abs(numeric_value - 20.0) < 0.1
                    score = 0.5 + (0.3 if realistic_tva else 0) + (0.2 if standard_tva else 0)
                    
                    confidence_scores["tva"] = score
                    
                    if score >= self.CONFIDENCE_THRESHOLDS["tva"]:
                        extracted_fields["tva"] = numeric_value
                        print(f"Champ extrait: tva = {numeric_value:.2f} (confiance: {score:.2f})")
                    else:
                        extracted_fields["tva"] = numeric_value
                        print(f"ATTENTION: Faible confiance pour tva = {numeric_value:.2f} (score: {score:.2f})")
                else:
                    confidence_scores["tva"] = 0.3
                    extracted_fields["tva"] = 0.0
                    print(f"ATTENTION: Format invalide pour tva: '{raw_value}' (score: 0.30)")
            except:
                confidence_scores["tva"] = 0.2
                extracted_fields["tva"] = 0.0
                print(f"ERREUR: Impossible d'extraire tva depuis '{raw_value}' (score: 0.20)")
        
        # 7. Total TTC
        if "TotalTTC" in entity_words and entity_words["TotalTTC"]:
            raw_value = entity_words["TotalTTC"][0]
            try:
                # Nettoyer et extraire la valeur
                cleaned_value = raw_value.replace("€", "").replace("EUR", "").replace(",", ".")
                import re
                match = re.search(r'(\d+(\.\d+)?)', cleaned_value)
                if match:
                    numeric_value = float(match.group(1))
                    # Score basé sur la présence d'un montant valide
                    realistic_amount = 1.0 <= numeric_value <= 120000.0
                    consistent_with_ht_tva = True
                    if "total_ht" in extracted_fields and "tva" in extracted_fields:
                        expected_ttc = extracted_fields["total_ht"] + extracted_fields["tva"]
                        consistent_with_ht_tva = abs(numeric_value - expected_ttc) < 1.0
                    
                    score = 0.5 + (0.3 if realistic_amount else 0) + (0.2 if consistent_with_ht_tva else 0)
                    
                    confidence_scores["total_ttc"] = score
                    
                    if score >= self.CONFIDENCE_THRESHOLDS["total_ttc"]:
                        extracted_fields["total_ttc"] = numeric_value
                        print(f"Champ extrait: total_ttc = {numeric_value:.2f} (confiance: {score:.2f})")
                    else:
                        extracted_fields["total_ttc"] = numeric_value
                        print(f"ATTENTION: Faible confiance pour total_ttc = {numeric_value:.2f} (score: {score:.2f})")
                else:
                    confidence_scores["total_ttc"] = 0.3
                    extracted_fields["total_ttc"] = 0.0
                    print(f"ATTENTION: Format invalide pour total_ttc: '{raw_value}' (score: 0.30)")
            except:
                confidence_scores["total_ttc"] = 0.2
                extracted_fields["total_ttc"] = 0.0
                print(f"ERREUR: Impossible d'extraire total_ttc depuis '{raw_value}' (score: 0.20)")
        
        # 8. Nom de l'entreprise
        if "CompanyName" in entity_words and entity_words["CompanyName"]:
            raw_value = entity_words["CompanyName"][0]
            # Score basé sur la longueur et la présence de lettres
            has_letters = any(c.isalpha() for c in raw_value)
            good_length = 3 <= len(raw_value) <= 100
            score = 0.4 + (0.3 if has_letters else 0) + (0.3 if good_length else 0)
            
            confidence_scores["company_name"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["company_name"]:
                extracted_fields["company_name"] = raw_value
                print(f"Champ extrait: company_name = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["company_name"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour company_name = '{raw_value}' (score: {score:.2f})")
        
        # 9. Numéro de TVA
        if "TVANumber" in entity_words and entity_words["TVANumber"]:
            raw_value = entity_words["TVANumber"][0]
            # Score basé sur le format du numéro de TVA
            import re
            has_fr_prefix = bool(re.search(r'FR\s*\d{2}', raw_value, re.IGNORECASE))
            has_digits = len(re.findall(r'\d', raw_value)) >= 8
            good_length = 9 <= len(raw_value) <= 20
            
            score = 0.3 + (0.3 if has_fr_prefix else 0) + (0.2 if has_digits else 0) + (0.2 if good_length else 0)
            confidence_scores["tva_number"] = score
            
            if score >= self.CONFIDENCE_THRESHOLDS["tva_number"]:
                extracted_fields["tva_number"] = raw_value
                print(f"Champ extrait: tva_number = '{raw_value}' (confiance: {score:.2f})")
            else:
                extracted_fields["tva_number"] = f"{raw_value} [?]"
                print(f"ATTENTION: Faible confiance pour tva_number = '{raw_value}' (score: {score:.2f})")
        
        # Score global basé sur le nombre de champs trouvés
        if len(entity_words) > 0:
            extracted_fields["confidence_score"] = min(len(entity_words) / 5 * 100, 100.0)
        else:
            extracted_fields["confidence_score"] = 0.0
        
        # Ajouter les scores de confiance au résultat
        extracted_fields["confidence_scores"] = confidence_scores
        
        return extracted_fields
    
    def _store_in_database(self, document_path, is_invoice, fields):
        """Store extraction results in MySQL database"""
        start_time = datetime.now()
        status = "SUCCESS"
        error_msg = None
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Convertir la date au format approprié
            date_str = fields.get("date", "")
            try:
                mysql_date = self._validate_and_normalize_french_date(date_str)
            except:
                mysql_date = None
            
            # Insérer les données
            cursor.execute(
                '''
                INSERT INTO invoices 
                (file_path, is_invoice, invoice_number, date_invoice, client_name, 
                 client_address, total_ht, tva, total_ttc, company_name, tva_number, 
                 confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                (
                    document_path,
                    int(is_invoice),
                    fields.get("invoice_number", ""),
                    mysql_date,
                    fields.get("client_name", ""),
                    fields.get("client_address", ""),  # Nouveau champ
                    fields.get("total_ht", 0.0),
                    fields.get("tva", 0.0),
                    fields.get("total_ttc", 0.0),
                    fields.get("company_name", ""),
                    fields.get("tva_number", ""),  # Nouveau champ
                    fields.get("confidence_score", 0.0),
                )
            )
            
            # Récupérer l'ID de la facture insérée
            invoice_id = cursor.lastrowid
            
            # Enregistrement des logs de confiance pour chaque champ
            if 'confidence_scores' in fields:
                confidence_scores = fields.pop('confidence_scores')  # Retirer du dict avant l'insertion
                
                for field_name, score in confidence_scores.items():
                    is_uncertain = score < self.CONFIDENCE_THRESHOLDS.get(field_name, 0.7)
                    
                    cursor.execute(
                        '''
                        INSERT INTO field_confidence_logs
                        (invoice_id, field_name, raw_value, confidence_score, is_uncertain)
                        VALUES (%s, %s, %s, %s, %s)
                        ''',
                        (
                            invoice_id,
                            field_name,
                            fields.get(field_name, ""),
                            score,
                            is_uncertain
                        )
                    )
                    
                    if is_uncertain:
                        print(f"Champ incertain: {field_name} = '{fields.get(field_name, '')}' (score: {score:.2f})")
            
            conn.commit()
            print(f"Données enregistrées en base pour {document_path}")
            
        except mysql.connector.Error as err:
            status = "ERROR"
            error_msg = str(err)
            print(f"Erreur lors de l'enregistrement en base: {err}")
        finally:
            # Calculer le temps de traitement en millisecondes
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Enregistrer dans extraction_logs
            try:
                if 'conn' not in locals() or not conn.is_connected():
                    conn = mysql.connector.connect(**self.db_config)
                    cursor = conn.cursor()
                    
                cursor.execute(
                    '''
                    INSERT INTO extraction_logs 
                    (file_processed, processing_time_ms, status, error_message, model_version)
                    VALUES (%s, %s, %s, %s, %s)
                    ''',
                    (
                        document_path,
                        processing_time,
                        status,
                        error_msg,
                        "v1.0"  # Version de votre modèle
                    )
                )
                conn.commit()
            except mysql.connector.Error as err:
                print(f"Erreur lors de l'enregistrement du log: {err}")
            finally:
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()
    
    def _validate_and_normalize_french_date(self, date_str):
        """
        Valide et normalise une date au format français (JJ/MM/AAAA) vers le format MySQL (AAAA-MM-JJ)
        Gère plusieurs formats possibles et les cas d'erreur OCR
        """
        if not date_str or len(date_str) < 6:  # Date trop courte
            return None
            
        import re
        
        # Nettoyer la chaîne (enlever caractères non numériques sauf séparateurs)
        date_str = date_str.strip()
        
        # Essayer différents formats de date française
        date_formats = [
            # Format JJ/MM/AAAA ou JJ/MM/AA
            r'(\d{1,2})[/\.\-](\d{1,2})[/\.\-](\d{2,4})',
            # Format sans séparateur clair JJMMAAAA ou JJMMAA
            r'(\d{1,2})(\d{2})(\d{2,4})',
            # Format avec espaces JJ MM AAAA
            r'(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})'
        ]
        
        for pattern in date_formats:
            match = re.search(pattern, date_str)
            if match:
                day, month, year = match.groups()
                
                # Convertir en entiers
                try:
                    day = int(day)
                    month = int(month)
                    year = int(year)
                    
                    # Valider les valeurs
                    if not (1 <= day <= 31) or not (1 <= month <= 12):
                        continue
                    
                    # Gérer les années abrégées (22 -> 2022)
                    if year < 100:
                        year = 2000 + year if year < 50 else 1900 + year
                    
                    # Vérification supplémentaire pour les jours par mois
                    days_in_month = [0, 31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if day > days_in_month[month]:
                        continue
                        
                    # Format MySQL
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except ValueError:
                    continue
        
        # Aucun format valide trouvé
        return None

    def standardize_bbox_format(self, bbox):
        """S'assurer que les coordonnées de boîtes sont au bon format"""
        if bbox is None:
            return None
        
        # Modifier pour garantir que les coordonnées sont au format attendu
        if len(bbox.shape) == 4 and bbox.shape[1] == 1:  # [batch, 1, seq, 4]
            # Supprimer la dimension 1
            bbox = bbox.squeeze(1)
        
        # S'assurer que la dernière dimension est bien 4 (x1, y1, x2, y2)
        if bbox.shape[-1] != 4:
            raise ValueError(f"Format de bbox incorrect: {bbox.shape}, doit se terminer par 4")
        
        return bbox


if __name__ == "__main__":
    # Example usage
    model = InvoiceModel()
    
    # Train the classifier
    model.train_classifier(
        "F:/Film_rec/dataset/training", 
        "F:/Film_rec/dataset/validation",
        negative_dir="F:/Film_rec/dataset/training/non_invoices"
    )
    
    # Process a sample document
    result = model.process_document("dataset/sample/facture_1.jpg")
    print(f"Is invoice: {result['is_invoice']}")
    if result['is_invoice']:
        print("Extracted fields:")
        for key, value in result['fields'].items():
            print(f"  {key}: {value}")