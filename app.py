from flask import Flask, request, jsonify, send_from_directory
import mysql.connector

app = Flask(__name__, static_folder='.')

# Database Configuration
DB_CONFIG = {
    'host': '',
    'user': '',
    'password': '',
    'database': '',
    'port': 3306
}

def get_db_connection():
    """Create and return a new database connection"""
    return mysql.connector.connect(**DB_CONFIG)

# Test database connection on startup
try:
    conn = get_db_connection()
    print("Database connected successfully")
    conn.close()
except Exception as e:
    print("Error connecting to database:", str(e))

# Static file routes
@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

# Stock Management Routes
@app.route('/stock_in')
def stock_in():
    """Handle stock in requests"""
    try:
        barcode = request.args.get('barcode')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE barcode_code = %s", (barcode,))
        item = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify(promptForDetails=item is None)
    except Exception as e:
        print("Stock In Error:", str(e))
        return jsonify(error=str(e)), 500

@app.route('/add_item')
def add_item():
    """Add new item to inventory"""
    try:
        barcode = request.args.get('barcode')
        item_name = request.args.get('item_name')
        price = request.args.get('price')
        quantity = request.args.get('quantity')
        
        conn = get_db_connection()
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
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Add Item Error:", str(e))
        return jsonify(error=str(e)), 500

@app.route('/update_stock')
def update_stock():
    """Update existing stock quantity"""
    try:
        barcode = request.args.get('barcode')
        quantity = request.args.get('quantity')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE stock_in SET quantity = quantity + %s WHERE barcode_code = %s",
                (quantity, barcode)
            )
            conn.commit()
            return jsonify(message="Stock quantity updated successfully.")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Update Stock Error:", str(e))
        return jsonify(error=str(e)), 500

# Cart Management Routes
@app.route('/stock_out')
def stock_out():
    """Handle stock out requests"""
    try:
        barcode = request.args.get('barcode')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # First check stock quantity
            cursor.execute("SELECT quantity FROM stock_in WHERE barcode_code = %s", (barcode,))
            stock = cursor.fetchone()
            
            if not stock or stock['quantity'] <= 0:
                return jsonify(message="This item is out of stock!")
            
            # Get item details
            cursor.execute("SELECT * FROM items WHERE barcode_code = %s", (barcode,))
            item = cursor.fetchone()
            
            if not item:
                return jsonify(message="Item not found in inventory.")
            
            # Update stock quantity and add to cart
            cursor.execute(
                "UPDATE stock_in SET quantity = quantity - 1 WHERE barcode_code = %s",
                (barcode,)
            )
            
            cursor.execute(
                "INSERT INTO cart (barcode_code, item_name, quantity, price_per_unit) VALUES (%s, %s, %s, %s)",
                (barcode, item['item_name'], 1, item['price_per_unit'])
            )
            
            conn.commit()
            return jsonify(message="Item added to cart and stock quantity updated.")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Stock Out Error:", str(e))
        return jsonify(error=str(e)), 500

@app.route('/view_cart')
def view_cart():
    """View cart contents"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT item_name, quantity, price_per_unit FROM cart")
            items = cursor.fetchall()
            return jsonify(items=items)
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("View Cart Error:", str(e))
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
