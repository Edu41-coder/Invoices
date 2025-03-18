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
    "B-InvoiceNum",    # Beginning of Invoice Number
    "I-InvoiceNum",    # Inside of Invoice Number
    "B-Date",          # Beginning of Date
    "I-Date",          # Inside of Date
    "B-CompanyName",   # Beginning of Company Name
    "I-CompanyName"    # Inside of Company Name
]

class InvoiceProcessor:
    def __init__(self, ocr_engine="tesseract"):
        """Initialize the invoice processor"""
        self.tokenizer = LayoutLMTokenizer.from_pretrained("microsoft/layoutlm-base-uncased")
        self.ocr_engine = ocr_engine
        
    def process_document(self, image_path):
        """Process a document image to extract text and layout information"""
        # Load image
        image = Image.open(image_path).convert("RGB")
        
        # Extract text and bounding boxes using OCR
        ocr_results = self._perform_ocr(image)
        
        # Convert OCR results to LayoutLM input format
        words, boxes, word_labels = self._prepare_layoutlm_input(ocr_results)
        
        # Tokenize and create model inputs
        inputs = self._tokenize(words, boxes)
        
        return {
            "image_path": image_path,
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
                    "box": [int(x1), int(y1), int(x2), int(y2)]
                })
        
        return results
    
    def _prepare_layoutlm_input(self, ocr_results):
        """Convert OCR results to LayoutLM input format"""
        words = []
        boxes = []
        word_labels = []  # For NER, initially all "O" (outside)
        
        for item in ocr_results:
            words.append(item["text"])
            boxes.append(item["box"])
            word_labels.append("O")  # Default label
            
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
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
            "bbox": torch.tensor(padded_boxes, dtype=torch.long)
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


class InvoiceDataset(Dataset):
    def __init__(self, data_dir, processor, is_classification=True, negative_dirs=None):
        """
        Dataset for invoice documents
        
        Args:
            data_dir: Directory containing invoice images
            processor: InvoiceProcessor instance
            is_classification: Whether this is for classification or NER
            negative_dirs: List of directory paths containing non-invoice documents
        """
        self.data_dir = Path(data_dir)
        self.processor = processor
        self.is_classification = is_classification
        
        # Collect all image paths
        self.image_paths = list(self.data_dir.glob('**/*.jpg')) + list(self.data_dir.glob('**/*.jpeg'))
        self.image_paths += list(self.data_dir.glob('**/*.pdf'))
        
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
        processed = self.processor.process_document(image_path)
        
        if self.is_classification:
            # For document classification
            return {
                **processed["inputs"],
                "labels": torch.tensor(self.labels[idx], dtype=torch.long)
            }
        else:
            # For NER
            # In real implementation, you'd load the NER labels for each token
            # Here we're just creating dummy labels (all "O")
            seq_length = processed["inputs"]["input_ids"].shape[1]
            token_labels = torch.zeros(seq_length, dtype=torch.long)  # All "O" labels
            
            return {
                **processed["inputs"],
                "labels": token_labels
            }


class InvoiceModel:
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
                    total_ht DECIMAL(10,2),
                    tva DECIMAL(10,2),
                    total_ttc DECIMAL(10,2),
                    company_name VARCHAR(100),
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence_score DECIMAL(5,2)
                )
                ''')
                print("Table 'invoices' créée avec succès.")
                
            # ... autres tables si nécessaire
            
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
        
        # Training setup
        optimizer = AdamW(self.classifier.parameters(), lr=learning_rate)
        
        # Training loop
        self.classifier.train()
        for epoch in range(epochs):
            print(f"Starting epoch {epoch + 1}/{epochs}")
            
            for batch in train_dataloader:
                # Move batch to GPU if available
                input_ids = batch["input_ids"].to(self.classifier.device)
                attention_mask = batch["attention_mask"].to(self.classifier.device)
                token_type_ids = batch["token_type_ids"].to(self.classifier.device)
                bbox = batch["bbox"].to(self.classifier.device)
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
                
            # Validation
            self.classifier.eval()
            val_loss = 0
            correct = 0
            total = 0
            
            with torch.no_grad():
                for batch in val_dataloader:
                    input_ids = batch["input_ids"].to(self.classifier.device)
                    attention_mask = batch["attention_mask"].to(self.classifier.device)
                    token_type_ids = batch["token_type_ids"].to(self.classifier.device)
                    bbox = batch["bbox"].to(self.classifier.device)
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
                    correct += (predictions == labels).sum().item()
                    total += labels.size(0)
            
            accuracy = correct / total
            print(f"Epoch {epoch + 1} - Validation Loss: {val_loss / len(val_dataloader):.4f}, Accuracy: {accuracy:.4f}")
            
            # Save the model after each epoch
            self.classifier.save_pretrained(self.model_dir / f"classifier_epoch_{epoch + 1}")
    
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
            "total_ht": 0.0,
            "tva": 0.0,
            "total_ttc": 0.0,
            "company_name": ""
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
            if pred_label.startswith("B-"):
                # Save previous entity if it exists
                if current_entity != "O" and current_text:
                    entity_type = current_entity.replace("B-", "").replace("I-", "")
                    entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
                
                # Start new entity
                current_entity = pred_label
                current_text = [word]
            
            # If we're inside an entity
            elif pred_label.startswith("I-") and current_entity != "O":
                # If the I- tag matches the current entity
                if pred_label.replace("I-", "B-") == current_entity:
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
                if current_entity != "O" and current_text:
                    entity_type = current_entity.replace("B-", "").replace("I-", "")
                    entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
                
                # Reset
                current_entity = "O"
                current_text = []
        
        # Don't forget the last entity
        if current_entity != "O" and current_text:
            entity_type = current_entity.replace("B-", "").replace("I-", "")
            entity_words[entity_type] = entity_words.get(entity_type, []) + [" ".join(current_text)]
        
        # Fill in the extracted fields
        if "InvoiceNum" in entity_words and entity_words["InvoiceNum"]:
            extracted_fields["invoice_number"] = entity_words["InvoiceNum"][0]
        
        if "Date" in entity_words and entity_words["Date"]:
            extracted_fields["date"] = entity_words["Date"][0]
        
        if "ClientName" in entity_words and entity_words["ClientName"]:
            extracted_fields["client_name"] = entity_words["ClientName"][0]
        
        if "TotalHT" in entity_words and entity_words["TotalHT"]:
            # Try to extract the numeric value
            try:
                total_ht_text = entity_words["TotalHT"][0]
                # Remove currency symbols and convert commas to dots
                total_ht_text = total_ht_text.replace("€", "").replace("EUR", "").replace(",", ".")
                # Extract numeric part
                import re
                match = re.search(r'(\d+(\.\d+)?)', total_ht_text)
                if match:
                    extracted_fields["total_ht"] = float(match.group(1))
            except:
                pass
        
        if "TVA" in entity_words and entity_words["TVA"]:
            # Similar to TotalHT
            try:
                tva_text = entity_words["TVA"][0]
                tva_text = tva_text.replace("€", "").replace("EUR", "").replace(",", ".")
                import re
                match = re.search(r'(\d+(\.\d+)?)', tva_text)
                if match:
                    extracted_fields["tva"] = float(match.group(1))
            except:
                pass
        
        if "TotalTTC" in entity_words and entity_words["TotalTTC"]:
            # Similar to TotalHT
            try:
                total_ttc_text = entity_words["TotalTTC"][0]
                total_ttc_text = total_ttc_text.replace("€", "").replace("EUR", "").replace(",", ".")
                import re
                match = re.search(r'(\d+(\.\d+)?)', total_ttc_text)
                if match:
                    extracted_fields["total_ttc"] = float(match.group(1))
            except:
                pass
        
        if "CompanyName" in entity_words and entity_words["CompanyName"]:
            extracted_fields["company_name"] = entity_words["CompanyName"][0]
        
        # Add confidence score
        extracted_fields["confidence_score"] = 0.0
        if len(entity_words) > 0:
            extracted_fields["confidence_score"] = min(len(entity_words) / 5 * 100, 100.0)  # Score based on number of fields found
        
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
                if "/" in date_str:
                    date_parts = date_str.split('/')
                    mysql_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    mysql_date = None
            except:
                mysql_date = None
            
            # Insérer les données
            cursor.execute(
                '''
                INSERT INTO invoices 
                (file_path, is_invoice, invoice_number, date_invoice, client_name, 
                 total_ht, tva, total_ttc, company_name, confidence_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                (
                    document_path,
                    int(is_invoice),
                    fields.get("invoice_number", ""),
                    mysql_date,
                    fields.get("client_name", ""),
                    fields.get("total_ht", 0.0),
                    fields.get("tva", 0.0),
                    fields.get("total_ttc", 0.0),
                    fields.get("company_name", ""),
                    fields.get("confidence_score", 0.0),
                )
            )
            
            # Récupérer l'ID de la facture insérée
            invoice_id = cursor.lastrowid
            
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