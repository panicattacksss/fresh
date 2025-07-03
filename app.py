from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'secret_key_123'

def init_db():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER NOT NULL,
                  cell TEXT NOT NULL,
                  quantity INTEGER NOT NULL,
                  last_updated TIMESTAMP,
                  FOREIGN KEY (product_id) REFERENCES products(id),
                  UNIQUE(product_id, cell))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS operations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER NOT NULL,
                  cell TEXT NOT NULL,
                  quantity INTEGER NOT NULL,
                  operation_type TEXT NOT NULL,
                  timestamp TIMESTAMP,
                  FOREIGN KEY (product_id) REFERENCES products(id))''')

    # Предзаполняем список товаров
    products = [
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
    
    for product in products:
        try:
            c.execute("INSERT OR IGNORE INTO products (name) VALUES (?)", (product,))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()

if not os.path.exists('warehouse.db'):
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        cell = request.form.get('cell')
        if cell:
            return redirect(url_for('operation', cell=cell))
        else:
            flash('Не удалось распознать QR-код', 'error')
    
    return render_template('scan.html')

@app.route('/operation/<cell>', methods=['GET', 'POST'])
def operation(cell):
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    c.execute("SELECT id, name FROM products ORDER BY name")
    products = c.fetchall()
    
    c.execute('''SELECT p.name, i.quantity 
                 FROM inventory i
                 JOIN products p ON i.product_id = p.id
                 WHERE i.cell = ?
                 ORDER BY p.name''', (cell,))
    current_items = c.fetchall()
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        action = request.form.get('action')
        
        if not product_id or not quantity:
            flash('Заполните все поля', 'error')
            return redirect(url_for('operation', cell=cell))
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                flash('Количество должно быть положительным числом', 'error')
                return redirect(url_for('operation', cell=cell))
        except ValueError:
            flash('Введите корректное количество', 'error')
            return redirect(url_for('operation', cell=cell))
        
        c.execute('''SELECT quantity FROM inventory 
                     WHERE product_id = ? AND cell = ?''', 
                     (product_id, cell))
        current = c.fetchone()
        
        if action == 'add':
            new_quantity = (current[0] if current else 0) + quantity
            if current:
                c.execute('''UPDATE inventory 
                             SET quantity = ?, last_updated = ?
                             WHERE product_id = ? AND cell = ?''', 
                             (new_quantity, datetime.now(), product_id, cell))
            else:
                c.execute('''INSERT INTO inventory 
                             (product_id, cell, quantity, last_updated)
                             VALUES (?, ?, ?, ?)''', 
                             (product_id, cell, quantity, datetime.now()))
            
            c.execute('''INSERT INTO operations 
                         (product_id, cell, quantity, operation_type, timestamp)
                         VALUES (?, ?, ?, ?, ?)''', 
                         (product_id, cell, quantity, 'add', datetime.now()))
            
            flash(f'Добавлено {quantity} единиц товара', 'success')
        
        elif action == 'remove':
            if not current or current[0] < quantity:
                flash('Недостаточно товара на складе', 'error')
                return redirect(url_for('operation', cell=cell))
            
            new_quantity = current[0] - quantity
            if new_quantity > 0:
                c.execute('''UPDATE inventory 
                             SET quantity = ?, last_updated = ?
                             WHERE product_id = ? AND cell = ?''', 
                             (new_quantity, datetime.now(), product_id, cell))
            else:
                c.execute('''DELETE FROM inventory 
                             WHERE product_id = ? AND cell = ?''', 
                             (product_id, cell))
            
            c.execute('''INSERT INTO operations 
                         (product_id, cell, quantity, operation_type, timestamp)
                         VALUES (?, ?, ?, ?, ?)''', 
                         (product_id, cell, quantity, 'remove', datetime.now()))
            
            flash(f'Списано {quantity} единиц товара', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('operation', cell=cell))
    
    conn.close()
    return render_template('operation.html', 
                         cell=cell, 
                         products=products, 
                         current_items=current_items)

@app.route('/inventory')
def inventory():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    c.execute('''SELECT i.cell, p.name, i.quantity 
                 FROM inventory i
                 JOIN products p ON i.product_id = p.id
                 ORDER BY i.cell, p.name''')
    items = c.fetchall()
    
    conn.close()
    return render_template('inventory.html', items=items)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)