import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

START, CHOOSE_ACTION, SELECT_PRODUCT, SELECT_RACK, SELECT_SHELF, ENTER_QUANTITY = range(6)

PRODUCTS = [
    "Круассан классический на сливочном масле 45 г",
    "Хлеб Бриошь на сливочном масле 180 г",
    "Багет ржаной половинка с чесноком 200г",
    "Багет пшеничный без добавления сахара 180 г",
    "Багет мультизлаковый 210 г",
    "Тартин злаковый 300 г",
    "Круассан с шоколадно-ореховой начинкой 90 г",
    "Хлеб Гречишный без добавления сахара 300 г",
    "Чиабатта со злаками 350 г",
    "Круассан миндальный на сливочном масле 90г",
    "Хлеб Чиабатта с оливками 270 г",
    "Хлеб Деревенский солодовый с семенами льна 280 г",
    "Булочка с кардамоном и корицей 90 г",
    "Тартин деревенский ржано-пшеничный 350 г",
    "Круассан миндальный с малиной 90 г",
    "Хлеб Тыквенный на закваске с семечками 250 г",
    "Хлеб на закваске Капустный с кислинкой 250 г",
    "Хлеб Монж 300 г",
    "Багет деревенский на закваске 140 г",
    "Хлеб ржаной с семечками 300 г",
    "Тосканский хлеб с итальянскими травами и оливковым маслом 250 г",
    "Скандинавский хлеб с вяленой клюквой и грецким орехом 300 г",
    "Хлеб Чиабатта Рустик 300 г",
    "Багет-половинка с чесноком 175 г",
    "Пирог сдобный Дабон с малиной 420 г, постный",
    "Горячая пицца Римская Мясная, 480 г",
    "Пирог сдобный с яблоком и корицей 420 г",
    "Пирог сдобный с творогом и лимоном 420 г",
    "Пирог осетинский с картофелем и сыром Картофджын 500 г"
]

def init_db():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        rack TEXT NOT NULL,
        shelf INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE(product_id, rack, shelf)
    )
    ''')
    
    for product in PRODUCTS:
        cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', (product,))
    
    conn.commit()
    conn.close()

def get_product_id_by_name(product_name):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_product_name_by_id(product_id):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Неизвестный товар"

def get_all_products():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM products')
    products = cursor.fetchall()
    conn.close()
    return products

def get_products_with_stock():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name 
        FROM products p
        JOIN inventory i ON p.id = i.product_id
        WHERE i.quantity > 0
        GROUP BY p.id
    ''')
    products = cursor.fetchall()
    conn.close()
    return products

def product_keyboard(action):
    keyboard = []
    
    if action == 'add':
        all_products = get_all_products()
        for product_id, product_name in all_products:
            keyboard.append([InlineKeyboardButton(product_name, callback_data=str(product_id))])
    else:
        products_with_stock = get_products_with_stock()
        if not products_with_stock:
            return None
        
        for product_id, product_name in products_with_stock:
            keyboard.append([InlineKeyboardButton(product_name, callback_data=str(product_id))])
    
    return InlineKeyboardMarkup(keyboard)

def get_racks_with_product(product_id):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT rack 
        FROM inventory 
        WHERE product_id = ? AND quantity > 0
    ''', (product_id,))
    racks = [rack[0] for rack in cursor.fetchall()]
    conn.close()
    return racks

def get_shelves_with_product(product_id, rack):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT shelf 
        FROM inventory 
        WHERE product_id = ? AND rack = ? AND quantity > 0
    ''', (product_id, rack))
    shelves = [shelf[0] for shelf in cursor.fetchall()]
    conn.close()
    return shelves

def rack_keyboard(product_id=None, action=None):
    keyboard = []
    
    if action == 'add' or not product_id:
        for rack in ['01', '02', '03']:
            keyboard.append([InlineKeyboardButton(rack, callback_data=rack)])
    else:
        racks = get_racks_with_product(product_id)
        if not racks:
            return None
        
        for rack in racks:
            keyboard.append([InlineKeyboardButton(rack, callback_data=rack)])
    
    return InlineKeyboardMarkup(keyboard)

def shelf_keyboard(product_id=None, rack=None, action=None):
    keyboard = []
    
    if action == 'add' or not product_id or not rack:
        for i in range(1, 7):
            keyboard.append([InlineKeyboardButton(str(i), callback_data=str(i))])
    else:
        shelves = get_shelves_with_product(product_id, rack)
        if not shelves:
            return None
        
        for shelf in shelves:
            keyboard.append([InlineKeyboardButton(str(shelf), callback_data=str(shelf))])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить на склад", callback_data="add")],
        [InlineKeyboardButton("Снять со склада", callback_data="remove")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    context.user_data['action'] = action
    
    reply_markup = product_keyboard(action)
    
    if not reply_markup:
        await query.edit_message_text("❌ На складе нет товаров для снятия!")
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text("Выберите товар:", reply_markup=reply_markup)
    return SELECT_PRODUCT

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data)
    product_name = get_product_name_by_id(product_id)
    
    context.user_data['product_id'] = product_id
    context.user_data['product_name'] = product_name
    
    action = context.user_data['action']
    reply_markup = rack_keyboard(product_id, action)
    
    if not reply_markup:
        await query.edit_message_text("❌ Для этого товара нет доступных стеллажей!")
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text("Выберите стеллаж:", reply_markup=reply_markup)
    return SELECT_RACK

async def select_rack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rack_num = query.data
    context.user_data['rack'] = rack_num
    
    action = context.user_data['action']
    product_id = context.user_data['product_id']
    reply_markup = shelf_keyboard(product_id, rack_num, action)
    
    if not reply_markup:
        await query.edit_message_text("❌ На этом стеллаже нет доступных полок с товаром!")
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.edit_message_text("Выберите полку:", reply_markup=reply_markup)
    return SELECT_SHELF

async def select_shelf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    shelf_num = int(query.data)
    rack_num = context.user_data['rack']
    
    shelf_code = f"400-{rack_num}-{str(shelf_num).zfill(2)}А"
    context.user_data['shelf'] = shelf_num
    context.user_data['shelf_code'] = shelf_code
    
    product_id = context.user_data['product_id']
    current_qty = get_current_quantity(product_id, rack_num, shelf_num)
    
    action_text = "добавления" if context.user_data['action'] == 'add' else "снятия"
    await query.edit_message_text(
        f"Товар: {context.user_data['product_name']}\n"
        f"Полка: {shelf_code}\n"
        f"Текущее количество: {current_qty} ед.\n\n"
        f"Введите количество для {action_text}:"
    )
    return ENTER_QUANTITY

def get_current_quantity(product_id, rack, shelf):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT quantity 
        FROM inventory 
        WHERE product_id = ? AND rack = ? AND shelf = ?
    ''', (product_id, rack, shelf))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def update_inventory(product_id: int, rack: str, shelf: int, quantity: int, action: str):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    
    current_qty = get_current_quantity(product_id, rack, shelf)
    
    if action == 'add':
        new_quantity = current_qty + quantity
        if current_qty > 0:
            cursor.execute('''
                UPDATE inventory 
                SET quantity = ? 
                WHERE product_id = ? AND rack = ? AND shelf = ?
            ''', (new_quantity, product_id, rack, shelf))
        else:
            cursor.execute('''
                INSERT INTO inventory (product_id, rack, shelf, quantity) 
                VALUES (?, ?, ?, ?)
            ''', (product_id, rack, shelf, new_quantity))
        conn.commit()
        conn.close()
        return True
    
    else:  # remove
        if current_qty < quantity:
            conn.close()
            return False
        
        new_quantity = current_qty - quantity
        if new_quantity > 0:
            cursor.execute('''
                UPDATE inventory 
                SET quantity = ? 
                WHERE product_id = ? AND rack = ? AND shelf = ?
            ''', (new_quantity, product_id, rack, shelf))
        else:
            cursor.execute('''
                DELETE FROM inventory 
                WHERE product_id = ? AND rack = ? AND shelf = ?
            ''', (product_id, rack, shelf))
        
        conn.commit()
        conn.close()
        return True

async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity = update.message.text
    user_data = context.user_data
    
    try:
        quantity = int(quantity)
        if quantity <= 0:
            await update.message.reply_text("Количество должно быть положительным числом! Повторите ввод:")
            return ENTER_QUANTITY
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите целое число:")
        return ENTER_QUANTITY

    product_id = user_data['product_id']
    product_name = user_data['product_name']
    rack = user_data['rack']
    shelf = user_data['shelf']
    shelf_code = user_data['shelf_code']
    action = user_data['action']
    
    success = update_inventory(product_id, rack, shelf, quantity, action)
    
    if not success and action == 'remove':
        current_qty = get_current_quantity(product_id, rack, shelf)
        await update.message.reply_text(
            f"❌ Ошибка! На полке только {current_qty} ед.\n"
            "Повторите попытку с другим количеством:"
        )
        return ENTER_QUANTITY
    
    action_text = "добавлено" if action == 'add' else "снято"
    current_qty = get_current_quantity(product_id, rack, shelf)
    
    await update.message.reply_text(
        f"✅ Успешно! {action_text.capitalize()} {quantity} ед. товара:\n"
        f"{product_name}\n"
        f"На полке: {shelf_code}\n"
        f"Текущий остаток: {current_qty} ед."
    )
    
    user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    context.user_data.clear()
    return ConversationHandler.END

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.name, i.rack, i.shelf, i.quantity 
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.quantity > 0
        ORDER BY p.name, i.rack, i.shelf
    ''')
    
    inventory_data = cursor.fetchall()
    conn.close()
    
    if not inventory_data:
        await update.message.reply_text("Склад пуст.")
        return
    
    message = "📦 Текущее состояние склада:\n\n"
    current_product = None
    
    for item in inventory_data:
        product, rack, shelf, quantity = item
        shelf_code = f"400-{rack}-{str(shelf).zfill(2)}А"
        
        if product != current_product:
            message += f"\n🍞 <b>{product}</b>\n"
            current_product = product
        
        message += f"  - Полка {shelf_code}: {quantity} ед.\n"
    
    await update.message.reply_text(message, parse_mode='HTML')

def main():
    init_db()
    
    application = Application.builder().token("7406551878:AAGE4YY5raXhhTf45yVkRY2Em-JznG883TY").build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_ACTION: [CallbackQueryHandler(choose_action)],
            SELECT_PRODUCT: [CallbackQueryHandler(select_product)],
            SELECT_RACK: [CallbackQueryHandler(select_rack)],
            SELECT_SHELF: [CallbackQueryHandler(select_shelf)],
            ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('inventory', inventory))
    
    application.run_polling()

if __name__ == '__main__':
    main()