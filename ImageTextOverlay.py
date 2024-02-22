from PIL import Image, ImageDraw, ImageFont
import torch
import numpy as np

class ImageTextOverlay:
    def __init__(self, device="cpu"):
        self.device = device
    _alignments = ["left", "right", "center"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"multiline": True, "default": "Hello"}),
                "textbox_width": ("INT", {"default": 200, "min": 1}),  
                "textbox_height": ("INT", {"default": 200, "min": 1}),  
                "max_font_size": ("INT", {"default": 30, "min": 1, "max": 256, "step": 1}),  
                "font": ("STRING", {"default": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}), 
                "alignment": (cls._alignments, {"default": "center"}),  
                "color": ("STRING", {"default": "#000000"}),  
                "start_x": ("INT", {"default": 0}),  
                "start_y": ("INT", {"default": 0}), 
                "padding": ("INT", {"default": 50}), 
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_text_overlay"
    CATEGORY = "image/text"

    def wrap_text_and_calculate_height(self, text, font, max_width):
        lines = []
        words = text.split()
        current_line = words[0]
        for word in words[1:]:
            # Test if adding a new word exceeds the max width
            test_line = current_line + ' ' + word
            test_line_bbox = font.getbbox(test_line)
            w = test_line_bbox[2] - test_line_bbox[0]  # Right - Left for width
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)  # Add the last line

        if lines:
            # Use getbbox to get the height of a single line
            single_line_bbox = font.getbbox(lines[0])
            single_line_height = single_line_bbox[3] - single_line_bbox[1]  # Bottom - Top for height
            total_height = len(lines) * single_line_height

        wrapped_text = '\n'.join(lines)
        return wrapped_text, total_height

    def add_text_overlay(self, image, text, textbox_width, textbox_height, max_font_size, font, alignment, color, start_x, start_y, padding):
        image_tensor = image
        image_np = image_tensor.cpu().numpy()
        image_pil = Image.fromarray((image_np.squeeze(0) * 255).astype(np.uint8))
        color_rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        # Adjust textbox dimensions for padding
        effective_textbox_width = textbox_width - 2 * padding
        effective_textbox_height = textbox_height - 2 * padding

        font_size = max_font_size
        while font_size >= 1:
            loaded_font = ImageFont.truetype(font, font_size)
            wrapped_text, total_text_height = self.wrap_text_and_calculate_height(text, loaded_font, effective_textbox_width)

            if total_text_height + 2 * padding <= textbox_height:
                draw = ImageDraw.Draw(image_pil)
                lines = wrapped_text.split('\n')
                y = start_y + padding + (effective_textbox_height - total_text_height) // 2

                for line in lines:
                    line_bbox = loaded_font.getbbox(line)
                    line_width = line_bbox[2] - line_bbox[0]  # Right - Left for width

                    if alignment == "left":
                        x = start_x + padding
                    elif alignment == "right":
                        x = start_x + textbox_width - line_width - padding
                    elif alignment == "center":
                        x = start_x + padding + (effective_textbox_width - line_width) // 2

                    draw.text((x, y), line, fill=color_rgb, font=loaded_font)
                    y += (line_bbox[3] - line_bbox[1])  # Bottom - Top for height

                break  # Break the loop if text fits within the specified dimensions

            font_size -= 1  # Decrease font size and try again

        image_tensor_out = torch.tensor(np.array(image_pil).astype(np.float32) / 255.0)
        image_tensor_out = torch.unsqueeze(image_tensor_out, 0)
        return (image_tensor_out,)


NODE_CLASS_MAPPINGS = {
    "Image Text Overlay": ImageTextOverlay,
}
