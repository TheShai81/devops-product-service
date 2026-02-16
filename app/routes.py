import os
from flask import Blueprint, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

product_bp = Blueprint("products", __name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT")
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


@product_bp.route("/products", methods=["GET"])
def get_all_products():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, product_name, price, product_description
            FROM products
        """)

        products = cursor.fetchall()
        return jsonify(products), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@product_bp.route("/products/<int:id>", methods=["GET"])
def get_one_product(id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, product_name, price, product_description
            FROM products
            WHERE id = %s
        """, (id,))

        product = cursor.fetchone()

        if not product:
            return jsonify({"error": "Product not found"}), 404

        return jsonify(product), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
