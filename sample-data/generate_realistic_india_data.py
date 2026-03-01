"""
Generate realistic Indian e-commerce data for return abuse detection
Mimics patterns from Flipkart/Amazon India
"""

import csv
import random
from datetime import datetime, timedelta
import numpy as np

random.seed(42)
np.random.seed(42)

# Real Indian cities with tier classification
TIER1_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad']
TIER2_CITIES = ['Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Bhopal', 'Visakhapatnam', 'Patna']
TIER3_CITIES = ['Ranchi', 'Raipur', 'Guwahati', 'Chandigarh', 'Mysore', 'Coimbatore', 'Kochi', 'Vadodara']

# Real Indian festivals (2026 dates)
FESTIVALS = [
    ('2026-01-14', 'Makar Sankranti'),
    ('2026-01-26', 'Republic Day'),
    ('2026-03-14', 'Holi'),
    ('2026-08-15', 'Independence Day'),
    ('2026-10-02', 'Gandhi Jayanti'),
    ('2026-10-24', 'Diwali'),
    ('2026-11-14', 'Diwali Sale Week'),
    ('2026-12-25', 'Christmas'),
]

# Product categories with realistic return rates
CATEGORIES = {
    'Fashion - Clothing': {'return_rate': 0.40, 'avg_price': 800, 'price_std': 500},
    'Fashion - Footwear': {'return_rate': 0.35, 'avg_price': 1500, 'price_std': 800},
    'Electronics - Mobile': {'return_rate': 0.15, 'avg_price': 15000, 'price_std': 8000},
    'Electronics - Laptop': {'return_rate': 0.12, 'avg_price': 45000, 'price_std': 20000},
    'Electronics - Accessories': {'return_rate': 0.25, 'avg_price': 500, 'price_std': 300},
    'Home & Kitchen': {'return_rate': 0.20, 'avg_price': 2000, 'price_std': 1500},
    'Beauty & Personal Care': {'return_rate': 0.18, 'avg_price': 600, 'price_std': 400},
    'Books': {'return_rate': 0.05, 'avg_price': 300, 'price_std': 200},
    'Sports & Fitness': {'return_rate': 0.22, 'avg_price': 1200, 'price_std': 800},
    'Toys & Baby Products': {'return_rate': 0.15, 'avg_price': 800, 'price_std': 500},
}

BRANDS = ['Samsung', 'Apple', 'OnePlus', 'Xiaomi', 'Realme', 'Nike', 'Adidas', 'Puma', 
          'Levi\'s', 'H&M', 'Zara', 'Boat', 'Noise', 'Prestige', 'Philips', 'Sony',
          'LG', 'Whirlpool', 'Lakme', 'Mamaearth', 'Generic Brand']

def is_festival_period(date):
    """Check if date is within 7 days of any festival"""
    for festival_date_str, _ in FESTIVALS:
        festival_date = datetime.strptime(festival_date_str, '%Y-%m-%d')
        if abs((date - festival_date).days) <= 7:
            return True
    return False

def generate_customer_profile():
    """Generate realistic customer profile"""
    profile_type = random.choices(
        ['genuine', 'occasional_returner', 'frequent_returner', 'abuser'],
        weights=[0.60, 0.25, 0.10, 0.05]
    )[0]
    
    if profile_type == 'genuine':
        base_return_rate = random.uniform(0.0, 0.15)
        total_orders = random.randint(5, 50)
        cod_preference = 0.3
    elif profile_type == 'occasional_returner':
        base_return_rate = random.uniform(0.15, 0.35)
        total_orders = random.randint(8, 40)
        cod_preference = 0.5
    elif profile_type == 'frequent_returner':
        base_return_rate = random.uniform(0.35, 0.60)
        total_orders = random.randint(10, 30)
        cod_preference = 0.7
    else:  # abuser
        base_return_rate = random.uniform(0.60, 0.90)
        total_orders = random.randint(15, 50)
        cod_preference = 0.85
    
    # City tier affects behavior
    city_tier = random.choices([1, 2, 3], weights=[0.40, 0.35, 0.25])[0]
    if city_tier == 1:
        city = random.choice(TIER1_CITIES)
    elif city_tier == 2:
        city = random.choice(TIER2_CITIES)
    else:
        city = random.choice(TIER3_CITIES)
    
    return {
        'profile_type': profile_type,
        'base_return_rate': base_return_rate,
        'total_orders': total_orders,
        'cod_preference': cod_preference,
        'city': city,
        'city_tier': city_tier
    }

# Generate 2000 customers
print("Generating 2000 customers...")
customers = []
customer_profiles = {}

for i in range(2000):
    customer_id = f"CUST{10000 + i}"
    profile = generate_customer_profile()
    
    registration_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))
    return_count = int(profile['total_orders'] * profile['base_return_rate'])
    
    customers.append({
        'customer_id': customer_id,
        'registration_date': registration_date.strftime('%Y-%m-%d'),
        'total_orders': profile['total_orders'],
        'return_count': return_count,
        'return_rate': round(profile['base_return_rate'], 2),
        'location': profile['city'],
        'preferred_payment': 'COD' if random.random() < profile['cod_preference'] else random.choice(['Prepaid', 'UPI', 'Card'])
    })
    
    customer_profiles[customer_id] = profile

with open('sample-data/customers.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
    writer.writeheader()
    writer.writerows(customers)

print(f"✓ Created {len(customers)} customers")

# Generate 500 products
print("Generating 500 products...")
products = []

for i in range(500):
    category = random.choice(list(CATEGORIES.keys()))
    cat_info = CATEGORIES[category]
    
    price = max(50, int(np.random.normal(cat_info['avg_price'], cat_info['price_std'])))
    return_rate = cat_info['return_rate'] + random.uniform(-0.05, 0.05)
    return_rate = max(0.01, min(0.95, return_rate))
    
    products.append({
        'product_id': f"PROD{10000 + i}",
        'category': category,
        'brand': random.choice(BRANDS),
        'price': price,
        'return_rate': round(return_rate, 2)
    })

with open('sample-data/products.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)

print(f"✓ Created {len(products)} products")

# Generate 10,000 orders
print("Generating 10,000 orders...")
orders = []
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 2, 28)

for i in range(10000):
    customer = random.choice(customers)
    customer_id = customer['customer_id']
    profile = customer_profiles[customer_id]
    
    product = random.choice(products)
    order_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    
    # Payment method based on customer preference
    if random.random() < profile['cod_preference']:
        payment_method = 'COD'
    else:
        payment_method = random.choice(['Prepaid', 'UPI', 'Card', 'Wallet'])
    
    is_festival = is_festival_period(order_date)
    
    orders.append({
        'order_id': f"ORD{100000 + i}",
        'customer_id': customer_id,
        'product_id': product['product_id'],
        'order_date': order_date.strftime('%Y-%m-%d'),
        'amount': product['price'],
        'payment_method': payment_method,
        'delivery_location': customer['location'],
        'is_festival_season': 1 if is_festival else 0,
        'category': product['category']
    })

with open('sample-data/orders.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows(orders)

print(f"✓ Created {len(orders)} orders")

# Generate returns with realistic patterns
print("Generating returns...")
returns = []
return_reasons = [
    'Size/fit issue',
    'Quality not as expected',
    'Defective product',
    'Wrong item received',
    'Changed mind',
    'Better price elsewhere',
    'Damaged in shipping',
    'Product not as described'
]

return_id = 10000
for order in orders:
    customer_id = order['customer_id']
    profile = customer_profiles[customer_id]
    product = next(p for p in products if p['product_id'] == order['product_id'])
    
    # Calculate return probability
    return_prob = profile['base_return_rate']
    
    # COD significantly increases return rate
    if order['payment_method'] == 'COD':
        return_prob += 0.25
    
    # Festival season abuse
    if order['is_festival_season']:
        return_prob += 0.20
    
    # High-value orders from risky customers
    if order['amount'] > 20000 and profile['base_return_rate'] > 0.4:
        return_prob += 0.15
    
    # Product category
    return_prob += (product['return_rate'] - 0.20)  # Adjust by category
    
    # Tier 3 cities have slightly higher return rates
    if profile['city_tier'] == 3:
        return_prob += 0.05
    
    # Cap probability
    return_prob = max(0.01, min(0.95, return_prob))
    
    # Decide if order is returned
    if random.random() < return_prob:
        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
        
        # Return timing (abusers return faster)
        if profile['profile_type'] == 'abuser':
            days_to_return = random.randint(1, 5)
        else:
            days_to_return = random.randint(2, 14)
        
        return_date = order_date + timedelta(days=days_to_return)
        
        returns.append({
            'return_id': f"RET{return_id}",
            'order_id': order['order_id'],
            'customer_id': customer_id,
            'return_date': return_date.strftime('%Y-%m-%d'),
            'reason': random.choice(return_reasons),
            'refund_amount': order['amount'],
            'days_to_return': days_to_return
        })
        return_id += 1

with open('sample-data/returns.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=returns[0].keys())
    writer.writeheader()
    writer.writerows(returns)

print(f"✓ Created {len(returns)} returns")

# Summary statistics
print("\n" + "="*60)
print("REALISTIC INDIAN E-COMMERCE DATA SUMMARY")
print("="*60)
print(f"Total Customers: {len(customers):,}")
print(f"Total Products: {len(products):,}")
print(f"Total Orders: {len(orders):,}")
print(f"Total Returns: {len(returns):,}")
print(f"Overall Return Rate: {len(returns)/len(orders)*100:.1f}%")

# Customer segments
genuine = sum(1 for c in customer_profiles.values() if c['profile_type'] == 'genuine')
occasional = sum(1 for c in customer_profiles.values() if c['profile_type'] == 'occasional_returner')
frequent = sum(1 for c in customer_profiles.values() if c['profile_type'] == 'frequent_returner')
abusers = sum(1 for c in customer_profiles.values() if c['profile_type'] == 'abuser')

print(f"\nCustomer Segments:")
print(f"  Genuine customers: {genuine} ({genuine/len(customers)*100:.1f}%)")
print(f"  Occasional returners: {occasional} ({occasional/len(customers)*100:.1f}%)")
print(f"  Frequent returners: {frequent} ({frequent/len(customers)*100:.1f}%)")
print(f"  Abusers: {abusers} ({abusers/len(customers)*100:.1f}%)")

# Payment analysis
cod_orders = sum(1 for o in orders if o['payment_method'] == 'COD')
cod_returns = sum(1 for r in returns if any(o['order_id'] == r['order_id'] and o['payment_method'] == 'COD' for o in orders))

print(f"\nPayment Method Analysis:")
print(f"  COD Orders: {cod_orders:,} ({cod_orders/len(orders)*100:.1f}%)")
print(f"  COD Returns: {cod_returns:,} ({cod_returns/len(returns)*100:.1f}% of all returns)")

# Festival analysis
festival_orders = sum(1 for o in orders if o['is_festival_season'])
festival_returns = sum(1 for r in returns if any(o['order_id'] == r['order_id'] and o['is_festival_season'] for o in orders))

print(f"\nFestival Season Analysis:")
print(f"  Festival Orders: {festival_orders:,} ({festival_orders/len(orders)*100:.1f}%)")
print(f"  Festival Returns: {festival_returns:,} ({festival_returns/len(returns)*100:.1f}% of all returns)")

# Category analysis
print(f"\nTop Return Categories:")
category_returns = {}
for order in orders:
    if any(r['order_id'] == order['order_id'] for r in returns):
        cat = order['category']
        category_returns[cat] = category_returns.get(cat, 0) + 1

for cat, count in sorted(category_returns.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {cat}: {count} returns")

print("\n✓ All files created in sample-data/ directory")
print("\nThis data mimics real Indian e-commerce patterns!")
print("Upload to S3 and retrain your model for much better accuracy.")
