import csv
from datetime import datetime
import psycopg
import os

from dotenv import load_dotenv

load_dotenv()

print("Password encontrada:", os.getenv("DB_PASSWORD") is not None)
conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="postgres",
    user="postgres",
    password=os.getenv("DB_PASSWORD")
)

found_missing = False
found_invalid_dates = False

total_orders = 0
total_sales = 0
sales_per_country = {}

with open('data/orders.csv', 'r', encoding='utf-8') as file:

    reader = csv.DictReader(file)

    for row_number, order in enumerate(reader, start=2):

        total_orders += 1

        quantity = int(order["quantity"])
        unit_price = float(order["unit_price"])

        total_price = quantity * unit_price

        total_sales += total_price
        country = order["country"]

        if country not in sales_per_country:
            sales_per_country[country] = 0

        sales_per_country[country] += total_price
        
        sql = """
    INSERT INTO orders (
        order_id,
        customer_id,
        product,
        category,
        quantity,
        unit_price,
        order_date,
        country,
        total_price
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
"""

        cursor = conn.cursor()
        cursor.execute(sql, (
            order['order_id'],
            order['customer_id'],
            order['product'],
            order['category'],
            order['quantity'],
            order['unit_price'],
            order['order_date'],
            order['country'],
            total_price
        ))


        for column, value in order.items():

            if value is None or value.strip() == '':
                print(f"Missing value in row {row_number}, column '{column}'")
                found_missing = True

        try:
            datetime.strptime(
                order["order_date"],
                "%Y-%m-%d"
            ).date()

        except (KeyError, TypeError, ValueError):
            print(f"Invalid date in row {row_number}: {order.get('order_date')}")
            found_invalid_dates = True

    average_order_value = total_sales / total_orders

    country_most_sales = max(
        sales_per_country,
        key=sales_per_country.get
    )
conn.commit()
cursor.close()
conn.close()

if not found_missing:
    print("No missing values found in the CSV file.")

if not found_invalid_dates:
    print("No invalid dates found in the CSV file.")

order_ids = set()

with open('data/orders.csv', 'r', encoding='utf-8') as file:

    reader = csv.DictReader(file)

    for row_number, order in enumerate(reader, start=2):

        order_id = order['order_id']

        if order_id in order_ids:
            print(f"Duplicate order_id '{order_id}' found in row {row_number}")
        else:
            order_ids.add(order_id)

print(f"Total Orders: {total_orders}")
print(f"Total Sales: {total_sales:.2f} €")
print(f"Average Order Value: {average_order_value:.2f} €")
print(f"Country with Most Sales: {country_most_sales}")    