import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

# Настройки
PAPER_WIDTH_MM = 297
PAPER_HEIGHT_MM = 105
DPI = 300 

def mm_to_pixels(mm, dpi):
    return int(mm * dpi / 25.4)

PAPER_WIDTH = mm_to_pixels(PAPER_WIDTH_MM, DPI)
PAPER_HEIGHT = mm_to_pixels(PAPER_HEIGHT_MM, DPI)

cells = [
    "Мороз_01_01_01", "Мороз_01_01_02", "Мороз_01_01_03", "Мороз_01_01_04",
    "Мороз_02_01_01", "Мороз_02_01_02", "Мороз_02_01_03", "Мороз_02_02_01",
    "Мороз_02_02_02", "Мороз_02_02_03", "Мороз_02_03_01", "Мороз_02_03_02",
    "Мороз_02_03_03", "Мороз_03_01_01", "Мороз_03_01_02", "Мороз_03_01_03",
    "Мороз_03_02_01", "Мороз_03_02_02", "Мороз_03_02_03", "Мороз_03_03_01",
    "Мороз_03_03_02", "Мороз_03_03_03", "Холод_01_01", "Холод_01_02",
    "Холод_01_03", "Холод_01_04", "Холод_01_05", "Холод_02_01",
    "Холод_02_02", "Холод_02_03", "Холод_02_04", "Холод_02_05",
    "Холод_03_01", "Холод_03_02", "Холод_03_03", "Холод_03_04", "Холод_03_05"
]

if not os.path.exists('qr_codes'):
    os.makedirs('qr_codes')

# Настройки QR-кода
QR_SIZE = mm_to_pixels(50, DPI)  
QR_BORDER = 2
FONT_SIZE = mm_to_pixels(6, DPI) 
MARGIN = mm_to_pixels(5, DPI)  

try:
    font = ImageFont.truetype("arial.ttf", FONT_SIZE)
except:
    font = ImageFont.load_default()

for cell in cells:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  
        box_size=10,
        border=QR_BORDER,
    )
    qr.add_data(cell)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE))
    
    img_width = QR_SIZE + 2 * MARGIN
    img_height = QR_SIZE + FONT_SIZE + 3 * MARGIN
    
    img = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(img)
    
    img.paste(qr_img, (MARGIN, MARGIN))
    
    text_width = draw.textlength(cell, font=font)
    text_x = (img_width - text_width) / 2
    text_y = QR_SIZE + 2 * MARGIN
    
    draw.text((text_x, text_y), cell, font=font, fill="black")
    
    img.save(f'qr_codes/{cell}.png', 'PNG', dpi=(DPI, DPI))

print(f"QR-коды успешно сгенерированы в папке qr_codes (размер для печати {PAPER_WIDTH_MM}x{PAPER_HEIGHT_MM} мм)")