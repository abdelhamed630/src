import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile


# ── Settings ──────────────────────────────────────────────────────────
MAX_SIZE        = (1200, 1200)   # أقصى حجم للصورة
THUMBNAIL_SIZE  = (400, 400)     # حجم الـ thumbnail
QUALITY         = 85             # جودة الضغط (1-100)
WATERMARK_TEXT  = 'E-Commerce'   # نص الـ watermark — غيّره لاسم متجرك
WATERMARK_OPACITY = 80           # شفافية الـ watermark (0-255)
CONVERT_TO_WEBP = True           # تحويل لـ WebP


def process_image(image_field, watermark=True) -> ContentFile:
    """
    بتاخد ImageField وبترجع ContentFile جاهز للحفظ بعد:
    1. Resize
    2. Compression
    3. تحويل لـ WebP
    4. Watermark (اختياري)
    """
    img = Image.open(image_field)

    # تحويل لـ RGB لو RGBA أو غيره (عشان WebP / JPEG)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGBA')
    else:
        img = img.convert('RGB')

    # 1. Resize — مع الحفاظ على النسبة
    img.thumbnail(MAX_SIZE, Image.LANCZOS)

    # 2. Watermark
    if watermark:
        img = add_watermark(img, WATERMARK_TEXT)

    # 3. Compression + WebP
    output = BytesIO()
    if CONVERT_TO_WEBP:
        img.save(output, format='WEBP', quality=QUALITY, optimize=True)
        ext = 'webp'
    else:
        img.save(output, format='JPEG', quality=QUALITY, optimize=True)
        ext = 'jpg'

    output.seek(0)

    # اسم الملف الجديد بالامتداد الصح
    original_name = os.path.splitext(image_field.name)[0]
    new_name = f'{original_name}.{ext}'

    return ContentFile(output.read(), name=new_name)


def make_thumbnail(image_field) -> ContentFile:
    """
    بتعمل thumbnail صغير للصورة
    """
    img = Image.open(image_field)
    img = img.convert('RGB')
    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    output = BytesIO()
    img.save(output, format='WEBP', quality=80, optimize=True)
    output.seek(0)

    original_name = os.path.splitext(image_field.name)[0]
    new_name = f'{original_name}_thumb.webp'

    return ContentFile(output.read(), name=new_name)


def add_watermark(img: Image.Image, text: str) -> Image.Image:
    """
    بتضيف watermark نصي في كل أركان الصورة بشكل خفيف
    """
    # نسخة RGBA عشان نتحكم في الشفافية
    watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)

    width, height = img.size

    # حجم الفونت بناءً على حجم الصورة
    font_size = max(20, width // 20)

    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    # حساب حجم النص
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width  = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 20
    color   = (255, 255, 255, WATERMARK_OPACITY)

    # Watermark في الأركان الأربعة
    positions = [
        (padding, padding),                                           # أعلى يسار
        (width - text_width - padding, padding),                      # أعلى يمين
        (padding, height - text_height - padding),                    # أسفل يسار
        (width - text_width - padding, height - text_height - padding), # أسفل يمين
        # وسط الصورة
        ((width - text_width) // 2, (height - text_height) // 2),
    ]

    for pos in positions:
        draw.text(pos, text, font=font, fill=color)

    # دمج الـ watermark مع الصورة الأصلية
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    combined = Image.alpha_composite(img, watermark_layer)
    return combined.convert('RGB')
