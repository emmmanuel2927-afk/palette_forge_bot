"""
🎨 Palette Forge Bot - Professional Color Palette Generator
Create beautiful color palettes with harmony rules, extract from images, and more!
"""

import os
import io
import random
import json
import math
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ==================== CONFIGURATION ====================

# Try multiple possible token variable names
BOT_TOKEN = (
    os.environ.get("TELEGRAM_TOKEN") or
    os.environ.get("TELEGRAM_BOT_TOKEN") or
    os.environ.get("BOT_TOKEN")
)

# If token is not set, try reading from .env file
if not BOT_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        BOT_TOKEN = (
            os.environ.get("TELEGRAM_TOKEN") or
            os.environ.get("TELEGRAM_BOT_TOKEN") or
            os.environ.get("BOT_TOKEN")
        )
    except:
        pass

# If still no token, show error
if not BOT_TOKEN:
    print("=" * 60)
    print("❌ ERROR: No Telegram Bot Token found!")
    print("=" * 60)
    print("Please set one of these environment variables:")
    print("  - TELEGRAM_TOKEN")
    print("  - TELEGRAM_BOT_TOKEN")
    print("  - BOT_TOKEN")
    print("=" * 60)
    print("In Railway:")
    print("1. Go to your project dashboard")
    print("2. Click on 'Variables' tab")
    print("3. Add variable: TELEGRAM_TOKEN = your_bot_token")
    print("4. Click 'Deploy'")
    print("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Palette Forge Bot"
BOT_USERNAME = "palette_forge_bot"
BOT_VERSION = "1.0.0"

# ==================== CONSTANTS ====================

# Color Harmony Rules
HARMONY_RULES = {
    "monochromatic": {"label": "🎨 Monochromatic", "count": 5, "description": "Single color with variations"},
    "complementary": {"label": "🔄 Complementary", "count": 2, "description": "Colors opposite on color wheel"},
    "analogous": {"label": "🌈 Analogous", "count": 5, "description": "Adjacent colors on color wheel"},
    "triadic": {"label": "🔺 Triadic", "count": 3, "description": "Three evenly spaced colors"},
    "tetradic": {"label": "🔲 Tetradic", "count": 4, "description": "Two complementary pairs"},
    "square": {"label": "⬜ Square", "count": 4, "description": "Four evenly spaced colors"},
    "split_complementary": {"label": "✂️ Split Complementary", "count": 3, "description": "Base + two adjacent complements"},
    "double_split": {"label": "✨ Double Split", "count": 4, "description": "Two complementary pairs split"},
}

# Common Colors for quick access
COMMON_COLORS = {
    "🔴 Red": "#FF0000",
    "🔵 Blue": "#0000FF",
    "🟢 Green": "#00FF00",
    "🟡 Yellow": "#FFFF00",
    "🟣 Purple": "#800080",
    "🟠 Orange": "#FFA500",
    "🩷 Pink": "#FFC0CB",
    "⚪ White": "#FFFFFF",
    "⚫ Black": "#000000",
    "🟤 Brown": "#A52A2A",
    "🔶 Coral": "#FF7F50",
    "💙 Navy": "#000080",
    "💚 Lime": "#00FF00",
    "💛 Gold": "#FFD700",
    "💜 Violet": "#EE82EE",
    "🩵 Cyan": "#00FFFF",
    "🤍 Gray": "#808080",
    "❤️ Crimson": "#DC143C",
}

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    if user_id not in user_data:
        user_data[user_id] = {
            "settings": {
                "harmony": "monochromatic",
                "count": 5,
                "last_generated": None
            },
            "history": [],
            "saved_palettes": []
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Palette", callback_data="generate")],
        [InlineKeyboardButton("🌈 Harmony Rules", callback_data="harmony")],
        [InlineKeyboardButton("🖼️ Extract from Image", callback_data="extract")],
        [InlineKeyboardButton("💾 Saved Palettes", callback_data="saved")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_harmony_keyboard():
    keyboard = []
    for harmony_id, harmony_data in HARMONY_RULES.items():
        keyboard.append([InlineKeyboardButton(
            f"{harmony_data['label']} - {harmony_data['description'][:20]}",
            callback_data=f"harmony_{harmony_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def get_count_keyboard():
    keyboard = [
        [InlineKeyboardButton("3 Colors", callback_data="count_3"),
         InlineKeyboardButton("4 Colors", callback_data="count_4")],
        [InlineKeyboardButton("5 Colors", callback_data="count_5"),
         InlineKeyboardButton("6 Colors", callback_data="count_6")],
        [InlineKeyboardButton("8 Colors", callback_data="count_8"),
         InlineKeyboardButton("10 Colors", callback_data="count_10")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_color_keyboard():
    keyboard = []
    colors = list(COMMON_COLORS.items())
    for i in range(0, len(colors), 3):
        row = []
        for j in range(3):
            if i + j < len(colors):
                name, hex_val = colors[i + j]
                row.append(InlineKeyboardButton(
                    name,
                    callback_data=f"color_{hex_val}"
                ))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def get_palette_options_keyboard():
    keyboard = [
        [InlineKeyboardButton("💾 Save Palette", callback_data="save_palette")],
        [InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")],
        [InlineKeyboardButton("🎨 Export as Image", callback_data="export")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_saved_palettes_keyboard(user_id: int):
    data = get_user_data(user_id)
    saved = data.get("saved_palettes", [])
    
    keyboard = []
    if saved:
        for idx, palette in enumerate(saved[-8:]):
            name = palette.get("name", f"Palette {idx+1}")
            colors = palette.get("colors", [])
            emojis = "".join(["⬛" for _ in colors[:3]])
            keyboard.append([InlineKeyboardButton(
                f"{emojis} {name}",
                callback_data=f"load_{idx}"
            )])
        keyboard.append([InlineKeyboardButton("🗑️ Clear All", callback_data="clear_saved")])
    else:
        keyboard.append([InlineKeyboardButton("📭 No saved palettes", callback_data="noop")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

# ==================== COLOR UTILITIES ====================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}"

def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL to RGB"""
    h = h / 360
    s = s / 100
    l = l / 100
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """Convert RGB to HSL"""
    r, g, b = r/255.0, g/255.0, b/255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2
    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        if max_c == r:
            h = ((g - b) / d) % 6
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h *= 60
        if h < 0:
            h += 360
    return (int(round(h)), int(round(s * 100)), int(round(l * 100)))

def generate_palette(base_color: str, harmony: str, count: int) -> List[str]:
    """Generate a color palette based on harmony rule"""
    rgb = hex_to_rgb(base_color)
    h, s, l = rgb_to_hsl(rgb[0], rgb[1], rgb[2])
    
    if harmony == "monochromatic":
        palette = []
        for i in range(count):
            new_l = max(10, min(90, l + (i - (count-1)/2) * 12))
            new_s = max(20, min(80, s + (i - (count-1)/2) * 5))
            rgb_val = hsl_to_rgb(h, new_s, new_l)
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "complementary":
        comp_h = (h + 180) % 360
        palette = [base_color]
        for i in range(count - 1):
            new_h = comp_h + (i - (count-2)/2) * 15
            rgb_val = hsl_to_rgb(new_h % 360, s, l)
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "analogous":
        palette = []
        for i in range(count):
            angle = h + (i - (count-1)/2) * 25
            rgb_val = hsl_to_rgb(angle % 360, s, l)
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "triadic":
        angles = [h, (h + 120) % 360, (h + 240) % 360]
        palette = []
        for i, angle in enumerate(angles):
            if i < count:
                new_s = s + (i - (count-1)/2) * 5
                new_l = l + (i - (count-1)/2) * 5
                rgb_val = hsl_to_rgb(angle, max(20, min(80, new_s)), max(10, min(90, new_l)))
                palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "tetradic":
        angles = [h, (h + 90) % 360, (h + 180) % 360, (h + 270) % 360]
        palette = []
        for i, angle in enumerate(angles[:count]):
            new_s = s + (i % 2) * 10
            new_l = l + (i // 2) * 10
            rgb_val = hsl_to_rgb(angle, max(20, min(80, new_s)), max(10, min(90, new_l)))
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "square":
        angles = [h, (h + 90) % 360, (h + 180) % 360, (h + 270) % 360]
        palette = []
        for i, angle in enumerate(angles[:count]):
            new_s = s + (i % 2) * 15
            new_l = l + (i // 2) * 10
            rgb_val = hsl_to_rgb(angle, max(20, min(80, new_s)), max(10, min(90, new_l)))
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "split_complementary":
        comp = (h + 180) % 360
        angles = [h, (comp - 30) % 360, (comp + 30) % 360]
        palette = []
        for i, angle in enumerate(angles[:count]):
            new_s = s + (i - (count-1)/2) * 10
            new_l = l + (i - (count-1)/2) * 5
            rgb_val = hsl_to_rgb(angle, max(20, min(80, new_s)), max(10, min(90, new_l)))
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    elif harmony == "double_split":
        comp = (h + 180) % 360
        angles = [h, (comp - 30) % 360, (comp + 30) % 360, (h + 60) % 360]
        palette = []
        for i, angle in enumerate(angles[:count]):
            new_s = s + (i % 2) * 15
            new_l = l + (i // 2) * 10
            rgb_val = hsl_to_rgb(angle, max(20, min(80, new_s)), max(10, min(90, new_l)))
            palette.append(rgb_to_hex(*rgb_val))
        return palette
    
    return [base_color]

def get_color_name(hex_color: str) -> str:
    """Get a simple color name from hex"""
    color_names = {
        "#FF0000": "Red", "#00FF00": "Green", "#0000FF": "Blue",
        "#FFFF00": "Yellow", "#FF00FF": "Magenta", "#00FFFF": "Cyan",
        "#000000": "Black", "#FFFFFF": "White", "#808080": "Gray",
        "#800080": "Purple", "#FFA500": "Orange", "#FFC0CB": "Pink",
        "#A52A2A": "Brown", "#FF7F50": "Coral", "#000080": "Navy",
        "#FFD700": "Gold", "#EE82EE": "Violet", "#DC143C": "Crimson"
    }
    return color_names.get(hex_color.upper(), "Custom")

def suggest_text_color(hex_color: str) -> str:
    """Suggest text color (black or white) for readability"""
    rgb = hex_to_rgb(hex_color)
    brightness = (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000
    return "#000000" if brightness > 128 else "#FFFFFF"

# ==================== IMAGE GENERATION ====================

def create_palette_image(colors: List[str], width: int = 800, height: int = 400) -> bytes:
    """Create a visual palette image with color swatches"""
    try:
        img = Image.new('RGB', (width, height), color='#F5F5F5')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        # Draw title
        draw.text((20, 15), "🎨 Palette Forge", fill=(50, 50, 50), font=font)
        draw.text((20, 45), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                 fill=(150, 150, 150), font=small_font)
        
        # Draw palette swatches
        swatch_width = (width - 60) // len(colors)
        swatch_height = height - 120
        y_offset = 80
        
        for i, color in enumerate(colors):
            x = 30 + i * swatch_width
            rgb = hex_to_rgb(color)
            
            # Draw swatch with rounded corners
            draw.rectangle([x, y_offset, x + swatch_width - 10, y_offset + swatch_height],
                          fill=rgb, outline=(200, 200, 200))
            
            # Draw hex code
            text = color.upper()
            text_color = suggest_text_color(color)
            try:
                bbox = draw.textbbox((0, 0), text, font=small_font)
                text_x = x + (swatch_width - 10 - (bbox[2] - bbox[0])) // 2
                text_y = y_offset + swatch_height + 10
                draw.text((text_x, text_y), text, fill=text_color, font=small_font)
            except:
                pass
        
        # Add footer
        footer = f"{len(colors)} colors"
        try:
            bbox = draw.textbbox((0, 0), footer, font=small_font)
            draw.text(((width - (bbox[2] - bbox[0])) // 2, height - 30), 
                     footer, fill=(150, 150, 150), font=small_font)
        except:
            pass
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', optimize=True)
        img_bytes.seek(0)
        return img_bytes.read()
        
    except Exception as e:
        print(f"Palette image error: {e}")
        return create_simple_palette(colors)

def create_simple_palette(colors: List[str]) -> bytes:
    """Create a simple fallback palette image"""
    try:
        height = 40 + len(colors) * 40
        img = Image.new('RGB', (300, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        for i, color in enumerate(colors):
            y = 20 + i * 40
            rgb = hex_to_rgb(color)
            draw.rectangle([20, y, 280, y + 30], fill=rgb)
            draw.text((290, y), color, fill=(0, 0, 0))
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.read()
    except:
        return b""

def extract_colors_from_image(image_data: bytes, count: int = 5) -> List[str]:
    """Extract dominant colors from an image"""
    try:
        img = Image.open(io.BytesIO(image_data))
        img = img.resize((100, 100))
        pixels = list(img.getdata())
        
        # Simple color quantization
        color_counts = {}
        for pixel in pixels:
            r = round(pixel[0] / 10) * 10
            g = round(pixel[1] / 10) * 10
            b = round(pixel[2] / 10) * 10
            key = (r, g, b)
            color_counts[key] = color_counts.get(key, 0) + 1
        
        # Sort by frequency
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Convert to hex
        colors = []
        for color, _ in sorted_colors[:count]:
            colors.append(rgb_to_hex(color[0], color[1], color[2]))
        
        return colors
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"🎨 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional color palette generator!\n\n"
        f"✨ **Features:**\n"
        f"• 🎨 Generate beautiful color palettes\n"
        f"• 🌈 8 Harmony Rules\n"
        f"• 🖼️ Extract colors from images\n"
        f"• 💾 Save your favorite palettes\n"
        f"• 📊 Usage statistics\n\n"
        f"📊 **Saved Palettes:** {len(data.get('saved_palettes', []))}\n\n"
        f"⬇️ Use the buttons below to get started!"
    )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 **{BOT_NAME} User Guide**\n\n"
        "**🎨 Generate Palette**\n"
        "• Click 'Generate Palette'\n"
        "• Choose a base color\n"
        "• Select harmony rule\n"
        "• Choose color count\n"
        "• Get your palette!\n\n"
        "**🌈 Harmony Rules**\n"
        "• Monochromatic - Single color variations\n"
        "• Complementary - Opposite colors\n"
        "• Analogous - Adjacent colors\n"
        "• Triadic - 3 evenly spaced colors\n"
        "• Tetradic - 2 complementary pairs\n"
        "• Square - 4 evenly spaced colors\n"
        "• Split Complementary - Base + 2 adjacent\n"
        "• Double Split - 2 complementary pairs\n\n"
        "**🖼️ Extract from Image**\n"
        "• Send any image\n"
        "• I'll extract dominant colors\n\n"
        "**💾 Saved Palettes**\n"
        "• Save your favorite palettes\n"
        "• Load them anytime\n\n"
        "**Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/generate - Generate palette"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== CALLBACK HANDLERS ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    settings = data["settings"]
    
    action = query.data
    
    # ===== MAIN ACTIONS =====
    
    if action == "generate":
        await query.edit_message_text(
            "🎨 **Select a base color**\n\n"
            "Choose a color to start your palette:",
            parse_mode="Markdown",
            reply_markup=get_color_keyboard()
        )
        context.user_data["action"] = "select_color"
        
    elif action == "harmony":
        await query.edit_message_text(
            "🌈 **Select Harmony Rule**\n\n"
            "Choose how colors should be generated:",
            parse_mode="Markdown",
            reply_markup=get_harmony_keyboard()
        )
        
    elif action == "extract":
        await query.edit_message_text(
            "🖼️ **Extract Colors from Image**\n\n"
            "Send me an image, and I'll extract the dominant colors!\n\n"
            "📸 Supported: JPG, PNG, WEBP",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "extract_waiting"
        
    elif action == "saved":
        await query.edit_message_text(
            "💾 **Saved Palettes**\n\n"
            "Your saved color palettes:",
            parse_mode="Markdown",
            reply_markup=get_saved_palettes_keyboard(user_id)
        )
        
    elif action == "stats":
        saved = len(data.get("saved_palettes", []))
        history = len(data.get("history", []))
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"🎨 Palettes Generated: {history}\n"
            f"💾 Saved Palettes: {saved}\n"
            f"🌈 Default Harmony: {settings.get('harmony', 'monochromatic').capitalize()}\n"
            f"📊 Default Count: {settings.get('count', 5)}\n"
            f"📅 Last Generated: {settings.get('last_generated', 'Never')}\n\n"
            f"🔢 Total Colors Used: {history * settings.get('count', 5)}"
        )
        
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "help":
        await help_command(update, context)
        
    elif action == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    # ===== HARMONY SELECTION =====
    
    elif action.startswith("harmony_"):
        harmony = action.replace("harmony_", "")
        if harmony in HARMONY_RULES:
            settings["harmony"] = harmony
            await query.edit_message_text(
                f"✅ **Harmony Updated!**\n\n"
                f"New harmony: {HARMONY_RULES[harmony]['label']}\n"
                f"Description: {HARMONY_RULES[harmony]['description']}\n\n"
                f"Generate a palette with /generate",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # ===== COUNT SELECTION =====
    
    elif action.startswith("count_"):
        count = int(action.replace("count_", ""))
        settings["count"] = count
        
        await query.edit_message_text(
            f"✅ **Count Updated!**\n\n"
            f"Number of colors: {count}\n\n"
            f"Generate a palette with /generate",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    # ===== COLOR SELECTION =====
    
    elif action.startswith("color_"):
        hex_color = action.replace("color_", "")
        context.user_data["base_color"] = hex_color
        
        await query.edit_message_text(
            f"✅ **Base Color Selected:** {hex_color}\n\n"
            f"Now choose a **harmony rule**:",
            parse_mode="Markdown",
            reply_markup=get_harmony_keyboard()
        )
        context.user_data["action"] = "select_harmony"
        
    # ===== SAVE PALETTE =====
    
    elif action == "save_palette":
        if "last_palette" not in context.user_data:
            await query.edit_message_text(
                "❌ No palette to save. Generate a palette first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        colors = context.user_data["last_palette"]
        harmony = settings.get("harmony", "monochromatic")
        
        palette_name = f"{harmony.capitalize()} Palette {len(data.get('saved_palettes', [])) + 1}"
        
        if "saved_palettes" not in data:
            data["saved_palettes"] = []
        
        data["saved_palettes"].append({
            "name": palette_name,
            "colors": colors,
            "harmony": harmony,
            "created": datetime.now().isoformat()
        })
        
        await query.edit_message_text(
            f"✅ **Palette Saved!**\n\n"
            f"📛 Name: {palette_name}\n"
            f"🎨 Colors: {len(colors)}\n"
            f"🌈 Harmony: {harmony.capitalize()}\n\n"
            f"View all saved palettes with /saved",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    # ===== LOAD SAVED =====
    
    elif action.startswith("load_"):
        idx = int(action.replace("load_", ""))
        saved = data.get("saved_palettes", [])
        
        if idx < len(saved):
            palette = saved[idx]
            colors = palette.get("colors", [])
            name = palette.get("name", f"Palette {idx+1}")
            
            # Generate image
            img_data = create_palette_image(colors)
            
            color_list = "\n".join([f"• {c}" for c in colors])
            
            await query.message.reply_photo(
                photo=io.BytesIO(img_data),
                caption=(
                    f"💾 **{name}**\n\n"
                    f"Colors:\n{color_list}\n\n"
                    f"🎨 Harmony: {palette.get('harmony', 'Unknown').capitalize()}\n"
                    f"📅 Created: {palette.get('created', 'Unknown')[:16]}"
                ),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # ===== CLEAR SAVED =====
    
    elif action == "clear_saved":
        if data.get("saved_palettes"):
            data["saved_palettes"] = []
            await query.edit_message_text(
                "🗑️ **All saved palettes cleared!**",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "📭 No saved palettes to clear.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # ===== REGENERATE =====
    
    elif action == "regenerate":
        if "last_palette" in context.user_data:
            colors = context.user_data["last_palette"]
            img_data = create_palette_image(colors)
            
            await query.message.reply_photo(
                photo=io.BytesIO(img_data),
                caption="🔄 **Regenerated Palette**\n\nUse /generate for a new one!",
                parse_mode="Markdown",
                reply_markup=get_palette_options_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ No palette to regenerate. Generate one first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # ===== EXPORT =====
    
    elif action == "export":
        if "last_palette" in context.user_data:
            colors = context.user_data["last_palette"]
            img_data = create_palette_image(colors)
            
            await query.message.reply_document(
                document=io.BytesIO(img_data),
                filename=f"palette_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                caption="📎 **Palette Exported!**\n\nDownload the image above.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ No palette to export. Generate one first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    # ===== NOOP =====
    
    elif action == "noop":
        await query.answer("Nothing to do here!")

# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    text = update.message.text.strip()
    
    # Check if user wants to generate from a hex code
    if text.startswith("#") and len(text) in [4, 7]:
        try:
            hex_to_rgb(text)
            # Generate palette from hex
            settings = data["settings"]
            harmony = settings.get("harmony", "monochromatic")
            count = settings.get("count", 5)
            
            colors = generate_palette(text, harmony, count)
            context.user_data["last_palette"] = colors
            
            # Update history
            if "history" not in data:
                data["history"] = []
            data["history"].append({
                "colors": colors,
                "harmony": harmony,
                "timestamp": datetime.now().isoformat()
            })
            settings["last_generated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            img_data = create_palette_image(colors)
            
            color_list = "\n".join([f"• {c}" for c in colors])
            
            await update.message.reply_photo(
                photo=io.BytesIO(img_data),
                caption=(
                    f"🎨 **Palette Generated!**\n\n"
                    f"Colors:\n{color_list}\n\n"
                    f"🌈 Harmony: {HARMONY_RULES[harmony]['label']}\n"
                    f"📊 Colors: {len(colors)}\n"
                    f"🎯 Base: {text}\n\n"
                    f"💾 Save with 'Save Palette' below!",
                ),
                parse_mode="Markdown",
                reply_markup=get_palette_options_keyboard()
            )
            return
        except:
            pass
    
    await update.message.reply_text(
        "👋 **Use the buttons below!**\n\n"
        "Or send a hex code like `#FF5733` to generate a palette!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages for color extraction"""
    action = context.user_data.get("action", "")
    
    if action != "extract_waiting":
        await update.message.reply_text(
            "🖼️ **Click 'Extract from Image' first!**",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    try:
        # Get the image
        photo = await update.message.photo[-1].get_file()
        image_data = await photo.download_as_bytearray()
        
        await update.message.reply_text(
            "🔄 **Extracting colors...**\n\n"
            "Analyzing your image for dominant colors.",
            parse_mode="Markdown"
        )
        
        # Extract colors
        colors = extract_colors_from_image(image_data, 6)
        
        if colors:
            img_data = create_palette_image(colors)
            
            color_list = "\n".join([f"• {c}" for c in colors])
            
            await update.message.reply_photo(
                photo=io.BytesIO(img_data),
                caption=(
                    f"🖼️ **Colors Extracted!**\n\n"
                    f"Found these dominant colors:\n{color_list}\n\n"
                    f"💾 Save this palette with the button below!",
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💾 Save Palette", callback_data="save_palette")],
                    [InlineKeyboardButton("🎨 Generate Palette", callback_data="generate")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
            
            context.user_data["last_palette"] = colors
            context.user_data["action"] = None
        else:
            await update.message.reply_text(
                "❌ **Failed to extract colors**\n\n"
                "Please try with a different image.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            
    except Exception as e:
        print(f"Image handling error: {e}")
        await update.message.reply_text(
            "❌ **Error processing image**\n\n"
            "Please try again with a different image.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== GENERATE COMMAND ====================

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    settings = data["settings"]
    
    await update.message.reply_text(
        "🎨 **Generate a Palette**\n\n"
        "Send me a color in any format:\n"
        "• Hex: `#FF5733`\n"
        "• Name: `blue`\n"
        "• RGB: `255, 87, 51`\n\n"
        "Or click a color below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 Red", callback_data="color_#FF0000"),
             InlineKeyboardButton("🔵 Blue", callback_data="color_#0000FF")],
            [InlineKeyboardButton("🟢 Green", callback_data="color_#00FF00"),
             InlineKeyboardButton("🟡 Yellow", callback_data="color_#FFFF00")],
            [InlineKeyboardButton("🟣 Purple", callback_data="color_#800080"),
             InlineKeyboardButton("🟠 Orange", callback_data="color_#FFA500")],
            [InlineKeyboardButton("⚫ Black", callback_data="color_#000000"),
             InlineKeyboardButton("⚪ White", callback_data="color_#FFFFFF")],
            [InlineKeyboardButton("🎨 More Colors", callback_data="generate")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
        ])
    )
    context.user_data["action"] = "select_color"

# ==================== MAIN ====================

async def post_init(application):
    print("=" * 60)
    print(f"🎨 {BOT_NAME} Started Successfully!")
    print(f"🤖 Username: @{BOT_USERNAME}")
    print(f"📦 Version: {BOT_VERSION}")
    print(f"🌈 Harmony Rules: {len(HARMONY_RULES)}")
    print(f"🎨 Common Colors: {len(COMMON_COLORS)}")
    print("=" * 60)
    print("✅ Bot is ready to serve users!")
    print("=" * 60)

def main():
    print(f"🚀 Starting {BOT_NAME}...")
    print(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    print("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
