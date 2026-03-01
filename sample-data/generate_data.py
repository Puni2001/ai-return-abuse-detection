"""
Generate synthetic e-commerce data for return abuse detection
Run this to create sample CSV files for testing
"""

import csv
import random
from datetime import datetime, timedelta

# Set seed for reproducibility
random.seed(42)

# Helper functions
def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_customer_id():
    return f"CUST{random.randint(1000, 9999)}"

def generate_order_id():
    return f"ORD{random.randint(100000, 999999)}"

def generate_product_id():
    return f"PROD{random.randint(1000, 9999)}"

# Generate Customers (200 customers)
print("Generating customers...")
customers = []
customer_ids = [generate_customer_id() for _ in range(200)]

for customer_id in customer_ids:
    # Create different customer profiles
    profile = random.choice(['good', 'good', 'good', 'medium', 'risky'])
    
    if profile == 'good':
        total_orders = random.randint(5, 20)
        return_count = random.randint(0, 2)
    elif profile == 'medium':
        total_orders = random.randint(3, 15)
        return_count = random.randint(1, 5)
    else:  # risky
        total_orders = random.randint(4, 12)
        return_count = random.randint(3, 10)
    
    return_rate = return_count / total_orders if total_orders > 0 else 0
    registration_date = random_date(datetime(2024, 1, 1), datetime(2025, 12, 31))
    
    customers.append({
        'customer_id': customer_id,
        'registration_date': registration_date.strftime('%Y-%m-%d'),
        'total_orders': total_orders,
        'return_count': return_count,
        'return_rate': round(return_rate, 2),
        'location': random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']),
        'preferred_payment': random.choice(['COD', 'COD', 'Prepaid', 'Prepaid', 'UPI'])
    })

# Write customers to CSV
with open('sample-data/customers.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
    writer.writeheader()
    writer.writerows(customers)

print(f"✓ Created {len(customers)} customers")

# Generate Products (100 products)
print("Generating products...")
products = []
categories = ['Electronics', 'Fashion', 'Home & Kitchen', 'Beauty', 'Books', 'Sports']

for i in range(100):
    category = random.choice(categories)
    
    # Different return rates by category
    if category == 'Fashion':
        base_return_rate = 0.35
    elif category == 'Electronics':
        base_return_rate = 0.25
    else:
        base_return_rate = 0.15
    
    products.append({
        'product_id': f"PROD{1000 + i}",
        'category': category,
        'brand': f"Brand{random.randint(1, 20)}",
        'price': random.randint(500, 50000),
        'return_rate': round(base_return_rate + random.uniform(-0.1, 0.1), 2)
    })

with open('sample-data/products.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)

print(f"✓ Created {len(products)} products")

# Generate Orders (1000 orders)
print("Generating orders...")
orders = []
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 2, 28)

for i in range(1000):
    customer = random.choice(customers)
    product = random.choice(products)
    order_date = random_date(start_date, end_date)
    
    # Festival season (Diwali, Holi, etc.)
    is_festival = order_date.month in [10, 11, 3]
    
    orders.append({
        'order_id': f"ORD{100000 + i}",
        'customer_id': customer['customer_id'],
        'product_id': product['product_id'],
        'order_date': order_date.strftime('%Y-%m-%d'),
        'amount': product['price'],
        'payment_method': customer['preferred_payment'],
        'delivery_location': customer['location'],
        'is_festival_season': 1 if is_festival else 0,
        'category': product['category']
    })

with open('sample-data/orders.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows(orders)

print(f"✓ Created {len(orders)} orders")

# Generate Returns (300 returns - 30% return rate)
print("Generating returns...")
returns = []
return_reasons = [
    'Defective product',
    'Wrong item received',
    'Size/fit issue',
    'Changed mind',
    'Better price elsewhere',
    'Quality not as expected',
    'Damaged in shipping'
]

# Select orders to return (STRONGER bias towards high-risk patterns)
orders_to_return = []
for order in orders:
    customer = next(c for c in customers if c['customer_id'] == order['customer_id'])
    product = next(p for p in products if p['product_id'] == order['product_id'])
    
    # Base return chance from customer behavior
    if customer['return_rate'] > 0.5:
        return_chance = 0.75  # Much higher for risky customers
    elif customer['return_rate'] > 0.3:
        return_chance = 0.45
    else:
        return_chance = 0.10  # Lower for good customers
    
    # COD orders are MUCH more likely to be returned
    if order['payment_method'] == 'COD':
        return_chance += 0.25
    
    # Festival season abuse
    if order['is_festival_season']:
        return_chance += 0.20
    
    # High-value orders from risky customers
    if order['amount'] > 20000 and customer['return_rate'] > 0.4:
        return_chance += 0.15
    
    # Product category matters
    if product['category'] in ['Fashion', 'Electronics']:
        return_chance += 0.10
    
    # Cap at 0.95
    return_chance = min(return_chance, 0.95)
    
    if random.random() < return_chance:
        orders_to_return.append(order)

# Create returns from selected orders
for i, order in enumerate(orders_to_return[:300]):
    order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
    return_date = order_date + timedelta(days=random.randint(1, 14))
    
    returns.append({
        'return_id': f"RET{10000 + i}",
        'order_id': order['order_id'],
        'customer_id': order['customer_id'],
        'return_date': return_date.strftime('%Y-%m-%d'),
        'reason': random.choice(return_reasons),
        'refund_amount': order['amount'],
        'days_to_return': (return_date - order_date).days
    })

with open('sample-data/returns.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=returns[0].keys())
    writer.writeheader()
    writer.writerows(returns)

print(f"✓ Created {len(returns)} returns")

# Generate summary statistics
print("\n" + "="*50)
print("DATA SUMMARY")
print("="*50)
print(f"Total Customers: {len(customers)}")
print(f"Total Products: {len(products)}")
print(f"Total Orders: {len(orders)}")
print(f"Total Returns: {len(returns)}")
print(f"Overall Return Rate: {len(returns)/len(orders)*100:.1f}%")

# Customer risk distribution
high_risk = sum(1 for c in customers if c['return_rate'] > 0.5)
medium_risk = sum(1 for c in customers if 0.3 <= c['return_rate'] <= 0.5)
low_risk = sum(1 for c in customers if c['return_rate'] < 0.3)

print(f"\nCustomer Risk Distribution:")
print(f"  High Risk (>50% return rate): {high_risk}")
print(f"  Medium Risk (30-50%): {medium_risk}")
print(f"  Low Risk (<30%): {low_risk}")

# Payment method analysis
cod_orders = sum(1 for o in orders if o['payment_method'] == 'COD')
cod_returns = sum(1 for r in returns if any(o['order_id'] == r['order_id'] and o['payment_method'] == 'COD' for o in orders))

print(f"\nPayment Method Analysis:")
print(f"  COD Orders: {cod_orders} ({cod_orders/len(orders)*100:.1f}%)")
print(f"  COD Returns: {cod_returns} ({cod_returns/len(returns)*100:.1f}% of all returns)")

print("\n✓ All files created in sample-data/ directory")
print("\nNext steps:")
print("1. Run: python sample-data/generate_data.py")
print("2. Upload CSV files to AWS S3")
print("3. Start building your ML model!")
