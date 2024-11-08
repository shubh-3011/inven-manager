from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
import os

app = Flask(__name__)

db_config = {
    'user': 'root',
    'password': 'shubh',
    'host': 'localhost',
    'database': 'project'
}

def db_connect():
    return mysql.connector.connect(**db_config)

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Stock In endpoint
@app.route('/stock_in')
def stock_in():
    barcode = request.args.get('barcode')
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items WHERE barcode_code = %s", (barcode,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(promptForDetails=item is None)

# Add item endpoint
@app.route('/add_item')
def add_item():
    barcode = request.args.get('barcode')
    item_name = request.args.get('item_name')
    price = request.args.get('price')
    quantity = request.args.get('quantity')
    
    conn = db_connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO items (barcode_code, item_name, price_per_unit) VALUES (%s, %s, %s)",
            (barcode, item_name, price)
        )
        cursor.execute(
            "INSERT INTO stock_in (barcode_code, item_name, quantity, price_per_unit) VALUES (%s, %s, %s, %s)",
            (barcode, item_name, quantity, price)
        )
        conn.commit()
        return jsonify(message="Item added and stock updated successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        cursor.close()
        conn.close()

# Update stock endpoint
@app.route('/update_stock')
def update_stock():
    barcode = request.args.get('barcode')
    quantity = request.args.get('quantity')
    
    conn = db_connect()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE stock_in SET quantity = quantity + %s WHERE barcode_code = %s",
            (quantity, barcode)
        )
        conn.commit()
        return jsonify(message="Stock quantity updated successfully.")
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        cursor.close()
        conn.close()

# Stock Out endpoint
@app.route('/stock_out')
def stock_out():
    barcode = request.args.get('barcode')
    
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM items WHERE barcode_code = %s", (barcode,))
        item = cursor.fetchone()
        
        if not item:
            return jsonify(message="Item not found in inventory.")
        
        cursor.execute(
            "UPDATE stock_in SET quantity = quantity - 1 WHERE barcode_code = %s AND quantity > 0",
            (barcode,)
        )
        
        cursor.execute(
            "INSERT INTO cart (barcode_code, item_name, quantity, price_per_unit) VALUES (%s, %s, %s, %s)",
            (barcode, item['item_name'], 1, item['price_per_unit'])
        )
        
        conn.commit()
        return jsonify(message="Item added to cart and stock quantity updated.")
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        cursor.close()
        conn.close()

# View Cart endpoint
@app.route('/view_cart')
def view_cart():
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT item_name, quantity FROM cart")
        items = cursor.fetchall()
        return jsonify(items=items)
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=3000)