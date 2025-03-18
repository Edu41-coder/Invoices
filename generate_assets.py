from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageOps, ImageFilter
import random
import os
import math
import numpy as np
from invoice_generator.config import ASSETS_DIR, COFFEE_STAINS_DIR, HANDWRITING_DIR, STAMPS_DIR, FOLDS_DIR, TEXTURES_DIR

def create_directory(dir_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

def generate_stamp(size=(300, 300), output_path=None):
    """Generate a random stamp with semi-transparent appearance"""
    # Create transparent background
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Choose stamp properties
    stamp_type = random.choice(['circle', 'square', 'rectangle', 'oval'])
    color = random.choice([
        (200, 0, 0, 100),    # Semi-transparent red
        (0, 0, 200, 100),    # Semi-transparent blue
        (0, 0, 0, 120),      # Semi-transparent black
        (128, 0, 128, 100),  # Semi-transparent purple
    ])
    
    # Calculate center and dimensions
    center_x, center_y = size[0] // 2, size[1] // 2
    width, height = random.randint(150, 250), random.randint(150, 250)
    
    # Draw the stamp shape
    if stamp_type == 'circle':
        radius = min(width, height) // 2
        draw.ellipse((center_x-radius, center_y-radius, center_x+radius, center_y+radius), 
                    outline=color, width=3)
        # Add inner circle
        inner_radius = radius - 20
        draw.ellipse((center_x-inner_radius, center_y-inner_radius, 
                     center_x+inner_radius, center_y+inner_radius), 
                    outline=color, width=2)
    elif stamp_type == 'square':
        half_side = min(width, height) // 2
        draw.rectangle((center_x-half_side, center_y-half_side, 
                       center_x+half_side, center_y+half_side), 
                      outline=color, width=3)
    elif stamp_type == 'rectangle':
        draw.rectangle((center_x-width//2, center_y-height//2, 
                       center_x+width//2, center_y+height//2), 
                      outline=color, width=3)
    elif stamp_type == 'oval':
        draw.ellipse((center_x-width//2, center_y-height//2, 
                     center_x+width//2, center_y+height//2), 
                    outline=color, width=3)
    
    # Add text
    try:
        font_size = random.randint(20, 40)
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    stamp_text = random.choice([
        "APPROUVÉ", "PAYÉ", "REÇU", 
        "CONFIDENTIEL", "COPIE", "ORIGINAL",
        "URGENT", "VALIDÉ"
    ])
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), stamp_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = center_x - text_width // 2
    text_y = center_y - text_height // 2
    
    # Draw text
    draw.text((text_x, text_y), stamp_text, fill=color, font=font)
    
    # Add random text at bottom (like a date)
    date_text = random.choice([
        "15/03/2023", "22/10/2022", "01/04/2024",
        "JAN 2023", "OCT 2022", "DÉC 2023"
    ])
    
    bottom_y = center_y + height//3
    date_bbox = draw.textbbox((0, 0), date_text, font=font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = center_x - date_width // 2
    
    draw.text((date_x, bottom_y), date_text, fill=color, font=font)
    
    # Rotate slightly for realism
    rotation = random.uniform(-15, 15)
    img = img.rotate(rotation, resample=Image.BICUBIC, expand=False)
    
    # Add some noise/imperfections
    img_array = np.array(img)
    noise = np.random.normal(0, 5, img_array.shape[:2])
    for i in range(3):  # Apply to RGB channels
        img_array[:,:,i] = np.clip(img_array[:,:,i] + noise, 0, 255)
    
    img = Image.fromarray(img_array.astype('uint8'), 'RGBA')
    
    # Save if output path is provided
    if output_path:
        img.save(output_path)
        print(f"Saved stamp to {output_path}")
    
    return img

def generate_handwriting(width=600, height=200, output_path=None):
    """Generate artificial handwriting"""
    # Create transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Choose ink color (semi-transparent)
    ink_color = random.choice([
        (0, 0, 200, 160),     # Semi-transparent blue
        (0, 0, 0, 180),       # Semi-transparent black
        (25, 25, 112, 160),   # Semi-transparent navy
        (139, 0, 0, 160)      # Semi-transparent dark red
    ])
    
    # Generate random handwriting effect
    style = random.choice(['signature', 'note', 'comment'])
    
    if style == 'signature':
        # Create a signature-like pattern
        points = []
        x, y = random.randint(50, 100), random.randint(height//2-20, height//2+20)
        length = random.randint(width//3, width//2)
        
        # Base line
        for i in range(length):
            y_var = math.sin(i/10) * random.randint(5, 15)
            points.append((x + i, y + y_var))
        
        # Add some loops and flourishes
        loop_x = x + random.randint(length//4, length//2)
        loop_y = y - random.randint(10, 30)
        loop_size = random.randint(20, 40)
        
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            lx = loop_x + loop_size * math.cos(rad)
            ly = loop_y + loop_size/2 * math.sin(rad)
            points.append((lx, ly))
        
        # Continue the base line
        for i in range(length//2):
            y_var = math.cos(i/8) * random.randint(5, 15)
            points.append((loop_x + i, y + y_var))
        
        # Draw the signature
        if len(points) >= 2:
            for i in range(len(points)-1):
                draw.line([points[i], points[i+1]], fill=ink_color, width=random.randint(2, 4))
    
    elif style == 'note':
        # Create short text-like lines
        line_count = random.randint(2, 4)
        start_y = random.randint(30, height//2)
        
        for line in range(line_count):
            line_y = start_y + line * random.randint(25, 35)
            line_length = random.randint(width//2, width-50)
            start_x = random.randint(20, 50)
            
            # Create word-like segments
            x = start_x
            while x < start_x + line_length:
                word_length = random.randint(20, 80)
                word_points = []
                
                # Generate a wavy line for a "word"
                for i in range(word_length):
                    y_var = math.sin(i/5) * random.randint(2, 6)
                    word_points.append((x + i, line_y + y_var))
                
                # Draw the word
                if len(word_points) >= 2:
                    for i in range(len(word_points)-1):
                        draw.line([word_points[i], word_points[i+1]], fill=ink_color, width=random.randint(1, 3))
                
                x += word_length + random.randint(10, 20)
    
    else:  # comment
        # Create a short comment/annotation with an arrow
        start_x = random.randint(width//2, width-100)
        start_y = random.randint(30, height-50)
        
        # Draw an arrow
        arrow_length = random.randint(50, 150)
        end_x = start_x - arrow_length
        end_y = start_y + random.randint(-30, 30)
        
        # Arrow line
        draw.line([(start_x, start_y), (end_x, end_y)], fill=ink_color, width=2)
        
        # Arrow head
        arrow_head_size = 10
        angle = math.atan2(end_y - start_y, end_x - start_x)
        angle1 = angle + math.pi/6
        angle2 = angle - math.pi/6
        
        draw.line([
            (end_x, end_y),
            (end_x + arrow_head_size * math.cos(angle1), 
             end_y + arrow_head_size * math.sin(angle1))
        ], fill=ink_color, width=2)
        
        draw.line([
            (end_x, end_y),
            (end_x + arrow_head_size * math.cos(angle2), 
             end_y + arrow_head_size * math.sin(angle2))
        ], fill=ink_color, width=2)
        
        # Add a short note near the arrow start
        note_points = []
        note_length = random.randint(30, 80)
        note_x = start_x
        note_y = start_y - random.randint(10, 20)
        
        for i in range(note_length):
            y_var = math.sin(i/4) * random.randint(2, 5)
            note_points.append((note_x + i, note_y + y_var))
        
        # Draw the note
        if len(note_points) >= 2:
            for i in range(len(note_points)-1):
                draw.line([note_points[i], note_points[i+1]], fill=ink_color, width=random.randint(1, 3))
    
    # Save if output path is provided
    if output_path:
        img.save(output_path)
        print(f"Saved handwriting to {output_path}")
    
    return img

def generate_coffee_stain(size=(300, 300), output_path=None):
    """Generate a coffee stain defect"""
    # Create transparent background
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw an irregular coffee stain shape
    center_x, center_y = size[0]//2, size[1]//2
    radius = random.randint(60, 100)
    
    # Generate random polygon points for stain
    points = []
    num_points = random.randint(15, 25)  # Plus de variabilité dans la forme
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        r = radius * (0.6 + 0.4 * random.random())  # Plus de variabilité dans le rayon
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)
        points.append((x, y))
    
    # Coffee stain color (semi-transparent brown) - variations de couleurs
    color = (
        random.randint(120, 160),  # R
        random.randint(60, 90),    # G
        random.randint(10, 30),    # B
        random.randint(40, 120)    # A (transparence)
    )
    
    draw.polygon(points, fill=color)
    
    # Add some texture/noise
    img_array = np.array(img)
    noise = np.random.normal(0, 10, img_array.shape[:2])
    for j in range(3):  # Apply to RGB channels
        img_array[:,:,j] = np.clip(img_array[:,:,j] + noise, 0, 255)
    
    # Ajouter des éclaboussures autour de la tache principale
    if random.random() > 0.5:
        for _ in range(random.randint(3, 8)):
            splash_x = center_x + random.randint(-radius, radius)
            splash_y = center_y + random.randint(-radius, radius)
            splash_size = random.randint(5, 15)
            splash_color = (color[0], color[1], color[2], color[3] // 2)  # Plus transparent
            draw.ellipse((
                splash_x - splash_size, 
                splash_y - splash_size, 
                splash_x + splash_size, 
                splash_y + splash_size), 
                fill=splash_color
            )
    
    # Appliquer un léger flou
    img = Image.fromarray(img_array.astype('uint8'), 'RGBA')
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # Save if output path is provided
    if output_path:
        img.save(output_path)
        print(f"Saved coffee stain to {output_path}")
    
    return img

def generate_fold(width=800, height=1100, output_path=None):
    """Generate a paper fold effect"""
    # Create transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Choose fold properties
    fold_type = random.choice(['horizontal', 'vertical', 'diagonal', 'corner'])
    
    # Color for the fold (semi-transparent dark gray to black)
    color_base = random.randint(20, 60)
    color_alpha = random.randint(30, 90)
    color = (color_base, color_base, color_base, color_alpha)
    
    # Generate fold based on type
    if fold_type == 'horizontal':
        # Position horizontale du pli
        y = random.randint(height//4, 3*height//4)
        line_width = random.randint(2, 4)
        
        # Dessiner la ligne horizontale
        draw.line([(0, y), (width, y)], fill=color, width=line_width)
        
        # Ajouter une ombre au pli
        for i in range(1, 5):
            shadow_color = (color[0], color[1], color[2], color[3]//2)
            draw.line([(0, y+i), (width, y+i)], fill=shadow_color, width=1)
    
    elif fold_type == 'vertical':
        # Position verticale du pli
        x = random.randint(width//4, 3*width//4)
        line_width = random.randint(2, 4)
        
        # Dessiner la ligne verticale
        draw.line([(x, 0), (x, height)], fill=color, width=line_width)
        
        # Ajouter une ombre au pli
        for i in range(1, 5):
            shadow_color = (color[0], color[1], color[2], color[3]//2)
            draw.line([(x+i, 0), (x+i, height)], fill=shadow_color, width=1)
    
    elif fold_type == 'diagonal':
        # Pli diagonal
        if random.choice([True, False]):
            draw.line([(0, 0), (width, height)], fill=color, width=random.randint(2, 4))
            # Ajouter une ombre au pli
            for i in range(1, 5):
                shadow_color = (color[0], color[1], color[2], color[3]//2)
                draw.line([(i, i), (width, height)], fill=shadow_color, width=1)
        else:
            draw.line([(width, 0), (0, height)], fill=color, width=random.randint(2, 4))
            # Ajouter une ombre au pli
            for i in range(1, 5):
                shadow_color = (color[0], color[1], color[2], color[3]//2)
                draw.line([(width-i, i), (0, height)], fill=shadow_color, width=1)
    
    else:  # corner fold
        # Coin du papier plié
        corner = random.choice(['top-left', 'top-right', 'bottom-left', 'bottom-right'])
        
        fold_size = random.randint(width//10, width//5)
        
        if corner == 'top-left':
            points = [(0, 0), (fold_size, 0), (0, fold_size)]
        elif corner == 'top-right':
            points = [(width, 0), (width - fold_size, 0), (width, fold_size)]
        elif corner == 'bottom-left':
            points = [(0, height), (fold_size, height), (0, height - fold_size)]
        else:  # bottom-right
            points = [(width, height), (width - fold_size, height), (width, height - fold_size)]
        
        # Dessiner le coin plié
        draw.polygon(points, fill=(240, 240, 240, 200), outline=color)
        
        # Ligne de pli
        draw.line([points[1], points[2]], fill=color, width=random.randint(1, 3))
        
        # Important: Modifier le nom du fichier si output_path est fourni
        if output_path:
            # Renommer pour inclure "corner" dans le nom du fichier
            output_path = output_path.replace("fold_", f"corner_fold_{corner}_")
    
    # Appliquer un léger flou
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Save if output path is provided
    if output_path:
        img.save(output_path)
        print(f"Saved fold effect to {output_path}")
    
    return img

def generate_texture(width=800, height=1100, output_path=None):
    """Generate a paper texture background"""
    # Create white background
    img = Image.new('RGB', (width, height), (255, 255, 255))
    
    # Choose texture type
    texture_type = random.choice(['noise', 'vintage', 'recycled', 'grid'])
    
    if texture_type == 'noise':
        # Create noise texture
        noise = np.random.normal(0, 10, (height, width))
        for y in range(height):
            for x in range(width):
                pixel = img.getpixel((x, y))
                noise_value = int(noise[y, x])
                new_value = max(240, min(255, pixel[0] + noise_value))
                img.putpixel((x, y), (new_value, new_value, new_value))
    
    elif texture_type == 'vintage':
        # Create yellowish vintage paper
        base_color = (random.randint(250, 255), random.randint(240, 250), random.randint(220, 240))
        img = Image.new('RGB', (width, height), base_color)
        
        # Add slight noise
        noise = np.random.normal(0, 7, (height, width))
        for y in range(height):
            for x in range(width):
                pixel = img.getpixel((x, y))
                noise_value = int(noise[y, x])
                r = max(230, min(255, pixel[0] + noise_value))
                g = max(220, min(250, pixel[1] + noise_value))
                b = max(200, min(240, pixel[2] + noise_value))
                img.putpixel((x, y), (r, g, b))
        
        # Add some random spots/stains
        for _ in range(random.randint(10, 30)):
            spot_x = random.randint(0, width)
            spot_y = random.randint(0, height)
            spot_size = random.randint(5, 20)
            spot_color = (
                random.randint(220, 245),
                random.randint(210, 235),
                random.randint(190, 220)
            )
            draw = ImageDraw.Draw(img)
            draw.ellipse(
                (spot_x - spot_size, spot_y - spot_size, 
                 spot_x + spot_size, spot_y + spot_size),
                fill=spot_color
            )
    
    elif texture_type == 'recycled':
        # Create grayish recycled paper look
        base_color = (random.randint(240, 250), random.randint(240, 250), random.randint(240, 250))
        img = Image.new('RGB', (width, height), base_color)
        
        # Add fiber-like texture
        draw = ImageDraw.Draw(img)
        for _ in range(500):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            length = random.randint(1, 10)
            angle = random.uniform(0, math.pi*2)
            x2 = x1 + length * math.cos(angle)
            y2 = y1 + length * math.sin(angle)
            fiber_color = (
                random.randint(200, 240),
                random.randint(200, 240),
                random.randint(200, 240)
            )
            draw.line([(x1, y1), (x2, y2)], fill=fiber_color, width=1)
        
        # Add small color specs
        for _ in range(300):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            spec_color = random.choice([
                (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)),
                (random.randint(220, 250), random.randint(220, 250), random.randint(180, 220))
            ])
            img.putpixel((x, y), spec_color)
    
    else:  # grid
        # Create subtle grid pattern
        draw = ImageDraw.Draw(img)
        grid_size = random.randint(15, 30)
        line_color = (random.randint(230, 245), random.randint(230, 245), random.randint(230, 245))
        
        # Draw horizontal lines
        for y in range(0, height, grid_size):
            draw.line([(0, y), (width, y)], fill=line_color, width=1)
        
        # Draw vertical lines
        for x in range(0, width, grid_size):
            draw.line([(x, 0), (x, height)], fill=line_color, width=1)
    
    # Apply slight blur for realism
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Save if output path is provided
    if output_path:
        img.save(output_path)
        print(f"Saved paper texture to {output_path}")
    
    return img

def main():
    # Utiliser les constantes de config.py
    create_directory(ASSETS_DIR)
    create_directory(STAMPS_DIR)
    create_directory(HANDWRITING_DIR)
    create_directory(COFFEE_STAINS_DIR)
    create_directory(FOLDS_DIR)
    create_directory(TEXTURES_DIR)
    
    # Generate stamps
    print("Generating stamps...")
    for i in range(10):
        generate_stamp(output_path=os.path.join(STAMPS_DIR, f"stamp_{i+1}.png"))
    
    # Generate handwriting
    print("Generating handwriting samples...")
    for i in range(10):
        generate_handwriting(output_path=os.path.join(HANDWRITING_DIR, f"handwriting_{i+1}.png"))
    
    # Generate coffee stains
    print("Generating coffee stain defects...")
    for i in range(10):  # Augmenté à 10
        generate_coffee_stain(output_path=os.path.join(COFFEE_STAINS_DIR, f"coffee_stain_{i+1}.png"))
    
    # Generate fold effects
    print("Generating fold effects...")
    # Générer des plis normaux (horizontaux, verticaux, diagonaux)
    for i in range(6):
        generate_fold(output_path=os.path.join(FOLDS_DIR, f"fold_{i+1}.png"))
    
    # Générer explicitement des plis de coin
    print("Generating corner fold effects...")
    corners = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
    for corner in corners:
        output_path = os.path.join(FOLDS_DIR, f"corner_fold_{corner}.png")
        img = Image.new('RGBA', (800, 1100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Paramètres du pli
        width, height = 800, 1100
        color_base = random.randint(20, 60)
        color_alpha = random.randint(30, 90)
        color = (color_base, color_base, color_base, color_alpha)
        fold_size = random.randint(width//10, width//5)
        
        # Déterminer les points selon le coin
        if corner == 'top-left':
            points = [(0, 0), (fold_size, 0), (0, fold_size)]
        elif corner == 'top-right':
            points = [(width, 0), (width - fold_size, 0), (width, fold_size)]
        elif corner == 'bottom-left':
            points = [(0, height), (fold_size, height), (0, height - fold_size)]
        else:  # bottom-right
            points = [(width, height), (width - fold_size, height), (width, height - fold_size)]
        
        # Dessiner le coin plié
        draw.polygon(points, fill=(240, 240, 240, 200), outline=color)
        draw.line([points[1], points[2]], fill=color, width=random.randint(1, 3))
        
        # Appliquer un léger flou et sauvegarder
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        img.save(output_path)
        print(f"Saved corner fold to {output_path}")
    
    # Generate paper textures
    print("Generating paper textures...")
    for i in range(10):
        generate_texture(output_path=os.path.join(TEXTURES_DIR, f"texture_{i+1}.png"))
    
    print("Asset generation complete!")

if __name__ == "__main__":
    main()