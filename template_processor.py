
from PIL import Image, ImageDraw, ImageFont
import io

def process_template_image(image_bytes: bytes, news_text: str) -> bytes:
    """
    Processes an image by adding news text below it.
    For demonstration, this function simply adds text. In a real scenario,
    it would merge with a template, add watermarks, etc.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB") # Ensure RGB for consistent processing

        # Define font and text color
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf", 30)
        except IOError:
            font = ImageFont.load_default() # Fallback to default font
        text_color = (0, 0, 0) # Black color

        # Calculate text size and new image height
        draw = ImageDraw.Draw(img)
        # A simple way to estimate text height, might need refinement for complex layouts
        # For Arabic text, Pillow's textsize can be tricky. This is a basic estimation.
        text_lines = []
        current_line = ""
        words = news_text.split()
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if draw.textlength(test_line, font=font) < img.width - 40: # 20px padding on each side
                current_line = test_line
            else:
                text_lines.append(current_line)
                current_line = word
        text_lines.append(current_line)

        line_height = font.getbbox("Tg")[3] - font.getbbox("Tg")[1] + 10 # Estimate line height with padding
        total_text_height = len(text_lines) * line_height

        new_height = img.height + total_text_height + 40 # 20px padding top/bottom for text area
        new_img = Image.new("RGB", (img.width, new_height), (255, 255, 255)) # White background
        new_img.paste(img, (0, 0))

        draw = ImageDraw.Draw(new_img)
        y_text = img.height + 20 # Start text 20px below the image
        for line in text_lines:
            # Center text (basic centering, might need adjustment for Arabic right-to-left)
            text_width = draw.textlength(line, font=font)
            x_text = (new_img.width - text_width) / 2
            draw.text((x_text, y_text), line, font=font, fill=text_color)
            y_text += line_height

        # Save the processed image to bytes
        output_buffer = io.BytesIO()
        new_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()
    except Exception as e:
        print(f"Error processing image: {e}")
        raise
