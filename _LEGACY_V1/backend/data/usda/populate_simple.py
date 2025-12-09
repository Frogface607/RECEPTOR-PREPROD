#!/usr/bin/env python3
"""
Simple USDA database population - debugging version
"""

import sqlite3
import os

# Simple test with 20 products first
foods_data = [
    (169057, 'Beef, loin, tenderloin steak, raw', 'Beef Products', '2019-04-01'),
    (173875, 'Chicken, broilers, breast, meat only, raw', 'Poultry Products', '2019-04-01'),
    (175001, 'Fish, salmon, Atlantic, raw', 'Fish', '2019-04-01'),
    (175174, 'Fish, cod, Atlantic, raw', 'Fish', '2019-04-01'),
    (170393, 'Potatoes, raw, skin on', 'Vegetables', '2019-04-01'),
    (169998, 'Carrots, raw', 'Vegetables', '2019-04-01'),
    (170000, 'Onions, raw', 'Vegetables', '2019-04-01'),
    (171265, 'Milk, whole, 3.25% milkfat', 'Dairy', '2019-04-01'),
    (171290, 'Egg, whole, raw, fresh', 'Eggs', '2019-04-01'),
    (168878, 'Rice, white, long-grain, raw', 'Grains', '2019-04-01'),
    (171413, 'Oil, olive, salad or cooking', 'Oils', '2019-04-01'),
    (170436, 'Salt, table', 'Spices', '2019-04-01'),
    (171325, 'Spices, pepper, black', 'Spices', '2019-04-01'),
    (169757, 'Sugars, granulated', 'Sweets', '2019-04-01'),
    (169640, 'Honey', 'Sweets', '2019-04-01'),
    (170457, 'Tomatoes, red, ripe, raw', 'Vegetables', '2019-04-01'),
    (169218, 'Cabbage, raw', 'Vegetables', '2019-04-01'),
    (169967, 'Broccoli, raw', 'Vegetables', '2019-04-01'),
    (171284, 'Butter, salted', 'Dairy', '2019-04-01'),
    (168841, 'Pasta, dry, enriched', 'Grains', '2019-04-01')
]

nutrients_data = [
    # Beef tenderloin (169057) - Kcal, Protein, Fat, Carbs
    (169057, 1008, 218), (169057, 1003, 22.2), (169057, 1004, 12.4), (169057, 1005, 0.0),
    # Chicken breast (173875)
    (173875, 1008, 165), (173875, 1003, 31.0), (173875, 1004, 3.6), (173875, 1005, 0.0),
    # Salmon (175001)
    (175001, 1008, 208), (175001, 1003, 20.0), (175001, 1004, 13.4), (175001, 1005, 0.0),
    # Cod (175174)
    (175174, 1008, 78), (175174, 1003, 17.5), (175174, 1004, 0.6), (175174, 1005, 0.0),
    # Potatoes (170393)
    (170393, 1008, 77), (170393, 1003, 2.0), (170393, 1004, 0.4), (170393, 1005, 16.1),
    # Carrots (169998)
    (169998, 1008, 35), (169998, 1003, 1.3), (169998, 1004, 0.1), (169998, 1005, 6.9),
    # Onions (170000)
    (170000, 1008, 41), (170000, 1003, 1.4), (170000, 1004, 0.2), (170000, 1005, 8.2),
    # Milk (171265)
    (171265, 1008, 64), (171265, 1003, 3.2), (171265, 1004, 3.6), (171265, 1005, 4.8),
    # Egg (171290)
    (171290, 1008, 157), (171290, 1003, 12.7), (171290, 1004, 11.5), (171290, 1005, 0.7),
    # Rice (168878)
    (168878, 1008, 365), (168878, 1003, 7.5), (168878, 1004, 2.6), (168878, 1005, 62.3),
    # Olive oil (171413)
    (171413, 1008, 898), (171413, 1003, 0.0), (171413, 1004, 99.8), (171413, 1005, 0.0),
    # Salt (170436)
    (170436, 1008, 0), (170436, 1003, 0.0), (170436, 1004, 0.0), (170436, 1005, 0.0),
    # Black pepper (171325)
    (171325, 1008, 251), (171325, 1003, 10.4), (171325, 1004, 3.3), (171325, 1005, 38.3),
    # Sugar (169757)
    (169757, 1008, 387), (169757, 1003, 0.0), (169757, 1004, 0.0), (169757, 1005, 99.8),
    # Honey (169640)
    (169640, 1008, 329), (169640, 1003, 0.8), (169640, 1004, 0.0), (169640, 1005, 81.5),
    # Tomatoes (170457)
    (170457, 1008, 20), (170457, 1003, 1.1), (170457, 1004, 0.2), (170457, 1005, 3.7),
    # Cabbage (169218)
    (169218, 1008, 27), (169218, 1003, 1.8), (169218, 1004, 0.1), (169218, 1005, 4.7),
    # Broccoli (169967)
    (169967, 1008, 28), (169967, 1003, 3.0), (169967, 1004, 0.4), (169967, 1005, 4.0),
    # Butter (171284)
    (171284, 1008, 748), (171284, 1003, 0.5), (171284, 1004, 82.5), (171284, 1005, 0.8),
    # Pasta (168841)
    (168841, 1008, 344), (168841, 1003, 10.4), (168841, 1004, 1.1), (168841, 1005, 71.5)
]

portions_data = [
    (171290, 'large egg', 50.0),
    (169057, '1 steak (6 oz)', 170.0),
    (173875, '1 breast, bone removed', 174.0),
    (175001, '1 fillet', 150.0),
    (170457, '1 medium tomato', 123.0),
    (169998, '1 medium carrot', 61.0),
    (170000, '1 medium onion', 110.0),
    (170393, '1 medium potato', 173.0),
    (171284, '1 tbsp', 14.2),
    (171413, '1 tbsp', 13.5)
]

def populate_usda_simple():
    db_path = 'usda.sqlite'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear tables
    cursor.execute("DELETE FROM foods")
    cursor.execute("DELETE FROM food_nutrient")  
    cursor.execute("DELETE FROM food_portion")
    
    # Insert data
    cursor.executemany('INSERT INTO foods VALUES (?, ?, ?, ?)', foods_data)
    cursor.executemany('INSERT INTO food_nutrient VALUES (?, ?, ?)', nutrients_data)
    cursor.executemany('INSERT INTO food_portion VALUES (?, ?, ?)', portions_data)
    
    conn.commit()
    conn.close()
    print(f"Successfully populated USDA database with {len(foods_data)} foods")

if __name__ == '__main__':
    populate_usda_simple()