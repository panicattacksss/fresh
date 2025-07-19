import os
import qrcode
import barcode
from barcode.writer import ImageWriter
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = "8045251218:AAEFxr1nB43Y0Df0D48CYa2W72RBoCdmi8g"

MODES = {
    'qr': 'QR-код',
    'barcode': 'Штрихкод'
}

def start(update: Update, context: CallbackContext) -> None:
    context.user_data['mode'] = 'qr'
    
    user = update.message.from_user
    update.message.reply_text(
        f"Привет, {user.first_name}!\n"
        "Отправь мне текст, и я сгенерирую код.\n"
        f"Текущий режим: {MODES['qr']}\n"
        "Используй /swap для переключения между QR-кодом и штрихкодом"
    )

def swap_mode(update: Update, context: CallbackContext) -> None:
    current_mode = context.user_data.get('mode', 'qr')
    new_mode = 'barcode' if current_mode == 'qr' else 'qr'
    context.user_data['mode'] = new_mode
    
    update.message.reply_text(
        f"Режим изменён!\n"
        f"Теперь я буду генерировать: {MODES[new_mode]}"
    )

def generate_code(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    mode = context.user_data.get('mode', 'qr')
    
    try:
        if mode == 'qr':
            filename = generate_qr_code(text)
        else:
            filename = generate_barcode(text)
        
        with open(filename, 'rb') as photo:
            update.message.reply_photo(photo=photo)
        
        os.remove(filename)
        
    except Exception as e:
        update.message.reply_text(f"Ошибка: {str(e)}")

def generate_qr_code(text: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = "qr_code.png"
    img.save(filename)
    
    return filename

def generate_barcode(text: str) -> str:
    if not text.isascii():
        raise ValueError("Штрихкод поддерживает только ASCII символы")
    
    code = barcode.get('code128', text, writer=ImageWriter())
    filename = code.save("barcode", options={'write_text': False})
    
    return f"{filename}" 

def main() -> None:
    """Запуск бота"""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("swap", swap_mode))
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, generate_code))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
