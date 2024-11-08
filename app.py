from flask import Flask, request, jsonify
import mysql.connector
import os

app = Flask(__name__)

# Database configuration using environment variables
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def get_db_connection():
    """Create a connection to the MySQL database."""
    return mysql.connector.connect(**db_config)

@app.route("/scan_barcode", methods=["POST"])
def scan_barcode():
    data = request.get_json()
    barcode = data.get("barcode")

    if not barcode:
        return jsonify({"error": "No barcode provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if item exists in the 'items' table
        cursor.execute("SELECT * FROM items WHERE barcode = %s", (barcode,))
        item = cursor.fetchone()

        if item:
            # If item exists, add it to 'stock_in' table with quantity
            cursor.execute("""
                INSERT INTO stock_in (barcode, item_name, quantity, price)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + 1
            """, (barcode, item['item_name'], 1, item['price']))
            conn.commit()
            return jsonify({"message": "Stock updated", "item": item}), 200
        else:
            # If item does not exist, request item details from the client
            return jsonify({"message": "Item not found. Provide name, quantity, and price"}), 404

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/add_new_item", methods=["POST"])
def add_new_item():
    data = request.get_json()
    barcode = data.get("barcode")
    item_name = data.get("item_name")
    quantity = data.get("quantity", 1)
    price = data.get("price")

    if not all([barcode, item_name, price]):
        return jsonify({"error": "Missing barcode, item name, or price"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Add item to 'items' table
        cursor.execute("""
            INSERT INTO items (barcode, item_name, price)
            VALUES (%s, %s, %s)
        """, (barcode, item_name, price))
        
        # Add item to 'stock_in' table with quantity
        cursor.execute("""
            INSERT INTO stock_in (barcode, item_name, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (barcode, item_name, quantity, price))
        conn.commit()

        return jsonify({"message": "Item added to inventory", "item": data}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/remove_from_stock", methods=["POST"])
def remove_from_stock():
    data = request.get_json()
    barcode = data.get("barcode")

    if not barcode:
        return jsonify({"error": "No barcode provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if item exists in 'stock_in' table and reduce quantity
        cursor.execute("SELECT * FROM stock_in WHERE barcode = %s", (barcode,))
        stock_item = cursor.fetchone()

        if stock_item and stock_item["quantity"] > 0:
            cursor.execute("""
                UPDATE stock_in
                SET quantity = quantity - 1
                WHERE barcode = %s
            """, (barcode,))
            conn.commit()

            # Add to 'cart' table for checkout
            cursor.execute("""
                INSERT INTO cart (barcode, item_name)
                VALUES (%s, %s)
            """, (barcode, stock_item['item_name']))
            conn.commit()
            return jsonify({"message": "Item removed from stock and added to cart"}), 200
        else:
            return jsonify({"error": "Item not in stock or quantity is zero"}), 404

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route("/view_cart", methods=["GET"])
def view_cart():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM cart")
        cart_items = cursor.fetchall()
        return jsonify({"cart": cart_items}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
