import os
from flask import Blueprint, jsonify, request, Response
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

load_dotenv()

product_bp = Blueprint("products", __name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT")
}

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


@product_bp.before_request
def before_request():
    request._start_time = time.time()

@product_bp.after_request
def after_request(response):
    endpoint = request.path
    method = request.method
    status = response.status_code

    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    if hasattr(request, '_start_time'):
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(time.time() - request._start_time)

    return response

@product_bp.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


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
