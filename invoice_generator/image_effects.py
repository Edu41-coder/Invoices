from PIL import Image, ImageEnhance, ImageDraw, ImageFilter, ImageOps
import numpy as np
import cv2
import random
import os
from datetime import datetime

class ImageEffects:
    def __init__(self, assets_dir="assets"):
        # Defect assets paths
        self.defect_assets = {
            "coffee_stains": self._load_defect_images(os.path.join(assets_dir, "coffee_stains")),
            "stamps": self._load_defect_images(os.path.join(assets_dir, "stamps")),
            "folds": self._load_defect_images(os.path.join(assets_dir, "folds"))
        }
        
        # Handwriting assets
        self.handwriting_assets = self._load_defect_images(os.path.join(assets_dir, "handwriting"))
        
        # Texture assets
        self.texture_assets = self._load_defect_images(os.path.join(assets_dir, "textures"))
    
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
        
    def _place_image_on_document(self, base_img, overlay_img, position_strategy='random', scale_range=(0.2, 0.5), defect_type=None):
        """
        Place an overlay image on the base image with specified positioning strategy
        
        Args:
            base_img: PIL Image - The base document image
            overlay_img: PIL Image - The image to overlay (defect, handwriting, etc)
            position_strategy: str - Positioning strategy ('random', 'totals', 'client', 'margin')
            scale_range: tuple - (min_scale, max_scale) for overlay image size
            defect_type: str - Type of defect being applied ('coffee_stains', 'folds', 'stamps', etc.)
            
        Returns:
            PIL Image - The base image with the overlay applied
        """
        # Resize overlay to a random size but keep aspect ratio
        width, height = overlay_img.size
        scale = random.uniform(scale_range[0], scale_range[1])
        new_width = int(base_img.width * scale)
        new_height = int(new_width * (height / width))
        overlay_img = overlay_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Traitement spécial pour les plis de coin
        if defect_type == 'folds' and ('corner' in getattr(overlay_img, 'filename', '') or 'coin' in getattr(overlay_img, 'filename', '')):
            # Déterminer quel coin utiliser en fonction de l'orientation du pli
            # Analyser l'image pour déterminer son orientation
            # (On suppose que la partie la plus claire correspond au coin plié)
            
            # Convertir en niveaux de gris pour analyse
            gray_overlay = overlay_img.convert('L')
            
            # Diviser l'image en quatre quadrants pour déterminer où se trouve la partie claire
            left_top = np.mean(np.array(gray_overlay.crop((0, 0, width//2, height//2))))
            right_top = np.mean(np.array(gray_overlay.crop((width//2, 0, width, height//2))))
            left_bottom = np.mean(np.array(gray_overlay.crop((0, height//2, width//2, height))))
            right_bottom = np.mean(np.array(gray_overlay.crop((width//2, height//2, width, height))))
            
            # Déterminer le coin le plus clair
            quadrants = [left_top, right_top, left_bottom, right_bottom]
            brightest = quadrants.index(max(quadrants))
            
            # Placer le pli dans le coin correspondant
            if brightest == 0:  # Coin supérieur gauche
                x, y = 0, 0
            elif brightest == 1:  # Coin supérieur droit
                x, y = base_img.width - overlay_img.width, 0
            elif brightest == 2:  # Coin inférieur gauche
                x, y = 0, base_img.height - overlay_img.height
            else:  # Coin inférieur droit
                x, y = base_img.width - overlay_img.width, base_img.height - overlay_img.height
        
        # Position standard pour les autres défauts
        elif position_strategy == 'random':
            # Position randomly anywhere on the document
            x = random.randint(0, max(1, base_img.width - overlay_img.width))
            y = random.randint(0, max(1, base_img.height - overlay_img.height))
        
        # Le reste du code reste inchangé...
        elif position_strategy == 'totals':
            # Bottom right - near totals
            x = base_img.width - overlay_img.width - random.randint(10, 50)
            y = int(base_img.height * 0.7) + random.randint(0, 100)
        
        elif position_strategy == 'client':
            # Top right - near client info
            x = base_img.width - overlay_img.width - random.randint(10, 50)
            y = int(base_img.height * 0.2) + random.randint(0, 100)
        
        elif position_strategy == 'margin':
            # Random margin
            if random.choice([True, False]):
                # Left or right margin
                x = random.choice([
                    random.randint(5, 50),  # Left
                    base_img.width - overlay_img.width - random.randint(5, 50)  # Right
                ])
                y = random.randint(50, base_img.height - overlay_img.height - 50)
            else:
                # Top or bottom margin
                x = random.randint(50, base_img.width - overlay_img.width - 50)
                y = random.choice([
                    random.randint(5, 50),  # Top
                    base_img.height - overlay_img.height - random.randint(5, 50)  # Bottom
                ])
        
        # Paste the overlay onto the base image
        base_img.paste(overlay_img, (x, y), overlay_img)
        
        return base_img
    
    def apply_texture(self, img):
        """Apply paper texture to the background of the document"""
        if not self.texture_assets:
            return img
        
        # Convert image to RGB if needed
        img_rgb = img.convert('RGB')
        
        # Select a random texture
        texture = random.choice(self.texture_assets)
        
        # Resize texture to match image size
        texture = texture.resize(img_rgb.size, Image.LANCZOS)
        
        # Convert texture to RGB mode
        texture_rgb = texture.convert('RGB')
        
        # Choose a blend mode
        blend_mode = random.choice(['overlay', 'multiply', 'screen'])
        
        # Apply different blending techniques based on the chosen mode
        if blend_mode == 'overlay':
            # Simple alpha blending
            alpha = random.uniform(0.1, 0.3)  # Subtlety of texture effect
            result = Image.blend(img_rgb, texture_rgb, alpha)
            
        elif blend_mode == 'multiply':
            # Multiply blend mode (darkens image)
            img_array = np.array(img_rgb).astype(float)
            texture_array = np.array(texture_rgb).astype(float) / 255.0
            
            # Apply multiply blend
            result_array = img_array * texture_array
            result_array = np.clip(result_array, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)
            
        else:  # screen mode
            # Screen blend mode (lightens image)
            img_array = np.array(img_rgb).astype(float) / 255.0
            texture_array = np.array(texture_rgb).astype(float) / 255.0
            
            # Apply screen blend
            result_array = 1 - (1 - img_array) * (1 - texture_array)
            result_array = (result_array * 255).astype(np.uint8)
            result = Image.fromarray(result_array)
        
        # Apply slight color adjustment to simulate aged paper
        if random.random() < 0.3:  # 30% chance for yellowed paper effect
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(0.9)  # Slightly reduce color saturation
            
            # Add a slight yellow/sepia tint
            r, g, b = result.split()
            r = r.point(lambda i: i * 1.05)  # Increase red slightly
            g = g.point(lambda i: i * 1.05)  # Increase green slightly
            b = b.point(lambda i: i * 0.9)   # Decrease blue slightly
            result = Image.merge('RGB', (r, g, b))
        
        return result
        
    def apply_defects(self, img):
        """Apply random defects like coffee stains, folds, or stamps"""
        img_rgba = img.convert('RGBA')
        defect_type = random.choice(['coffee_stains', 'folds', 'stamps', None])
        
        if defect_type and self.defect_assets[defect_type]:
            # Get a random defect image
            defect = random.choice(self.defect_assets[defect_type])
            
            # Place defect on document using the helper method
            img_rgba = self._place_image_on_document(
                img_rgba, 
                defect,
                position_strategy='random',
                scale_range=(0.2, 0.5),
                defect_type=defect_type  # Passer le type de défaut
            )
        
        # Apply fold effect directly to the image
        if defect_type == 'folds' or random.random() < 0.3:
            img_rgba = self.apply_fold_effect(img_rgba)
        
        return img_rgba.convert('RGB')
    
    def apply_fold_effect(self, img):
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
    
    def add_handwriting(self, img):
        """Add handwritten annotations to the image"""
        img_rgba = img.convert('RGBA')
        
        if self.handwriting_assets:
            # Get a random handwriting image
            handwriting = random.choice(self.handwriting_assets)
            
            # Choose a positioning strategy
            position_strategy = random.choice(['totals', 'client', 'margin'])
            
            # Place handwriting on document using the helper method
            img_rgba = self._place_image_on_document(
                img_rgba,
                handwriting,
                position_strategy=position_strategy,
                scale_range=(0.1, 0.3)  # Smaller than defects
            )
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

    def add_noise(self, img):
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