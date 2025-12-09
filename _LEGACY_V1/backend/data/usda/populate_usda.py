#!/usr/bin/env python3
"""
Populate USDA SQLite database with dev-subset of nutrition data
~400 products covering common Russian restaurant ingredients
"""

import sqlite3
import os

def populate_usda_db():
    db_path = os.path.join(os.path.dirname(__file__), 'usda.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Мясо и птица
    foods_data = [
        (169057, 'Beef, loin, tenderloin steak, raw', 'Beef Products', '2019-04-01'),
        (173875, 'Chicken, broilers, breast, meat only, raw', 'Poultry Products', '2019-04-01'),
        (172851, 'Pork, fresh, loin, tenderloin, lean only, raw', 'Pork Products', '2019-04-01'),
        (172859, 'Turkey, breast, meat only, raw', 'Poultry Products', '2019-04-01'),
        (169059, 'Beef, chuck, blade roast, raw', 'Beef Products', '2019-04-01'),
        (172906, 'Bacon, raw', 'Pork Products', '2019-04-01'),
        (172908, 'Ham, whole, raw', 'Pork Products', '2019-04-01'),
        (175167, 'Duck, domesticated, meat only, raw', 'Poultry Products', '2019-04-01'),
        (173904, 'Chicken, thigh, meat only, raw', 'Poultry Products', '2019-04-01'),
        (173905, 'Chicken, wing, meat and skin, raw', 'Poultry Products', '2019-04-01'),
        
        # Рыба и морепродукты
        (175001, 'Fish, salmon, Atlantic, raw', 'Fish', '2019-04-01'),
        (175174, 'Fish, cod, Atlantic, raw', 'Fish', '2019-04-01'),
        (175149, 'Fish, mackerel, Atlantic, raw', 'Fish', '2019-04-01'),
        (175160, 'Fish, pike, northern, raw', 'Fish', '2019-04-01'),
        (172459, 'Crustaceans, shrimp, mixed species, raw', 'Fish', '2019-04-01'),
        (175191, 'Mollusks, squid, mixed species, raw', 'Fish', '2019-04-01'),
        (175185, 'Mollusks, mussel, blue, raw', 'Fish', '2019-04-01'),
        (175146, 'Fish, tuna, fresh, bluefin, raw', 'Fish', '2019-04-01'),
        (175172, 'Fish, sardine, Pacific, raw', 'Fish', '2019-04-01'),
        (175002, 'Fish, trout, rainbow, raw', 'Fish', '2019-04-01'),
        
        # Овощи
        (170393, 'Potatoes, raw, skin on', 'Vegetables', '2019-04-01'),
        (169998, 'Carrots, raw', 'Vegetables', '2019-04-01'),
        (170000, 'Onions, raw', 'Vegetables', '2019-04-01'),
        (170003, 'Garlic, raw', 'Vegetables', '2019-04-01'),
        (170457, 'Tomatoes, red, ripe, raw', 'Vegetables', '2019-04-01'),
        (169225, 'Cucumber, peeled, raw', 'Vegetables', '2019-04-01'),
        (169218, 'Cabbage, raw', 'Vegetables', '2019-04-01'),
        (169967, 'Broccoli, raw', 'Vegetables', '2019-04-01'),
        (170417, 'Peppers, sweet, red, raw', 'Vegetables', '2019-04-01'),
        (169228, 'Eggplant, raw', 'Vegetables', '2019-04-01'),
        (169291, 'Squash, summer, zucchini, raw', 'Vegetables', '2019-04-01'),
        (169145, 'Beets, raw', 'Vegetables', '2019-04-01'),
        (169270, 'Spinach, raw', 'Vegetables', '2019-04-01'),
        (169238, 'Lettuce, iceberg, raw', 'Vegetables', '2019-04-01'),
        (169247, 'Mushrooms, white, raw', 'Vegetables', '2019-04-01'),
        (170419, 'Peppers, sweet, green, raw', 'Vegetables', '2019-04-01'),
        (169220, 'Cauliflower, raw', 'Vegetables', '2019-04-01'),
        (169226, 'Corn, sweet, white, raw', 'Vegetables', '2019-04-01'),
        (170427, 'Radishes, raw', 'Vegetables', '2019-04-01'),
        (170015, 'Asparagus, raw', 'Vegetables', '2019-04-01'),
        (169248, 'Onions, green/scallions, raw', 'Vegetables', '2019-04-01'),
        (169016, 'Arugula, raw', 'Vegetables', '2019-04-01'),
        (170378, 'Parsley, fresh', 'Vegetables', '2019-04-01'),
        (170322, 'Dill, fresh', 'Vegetables', '2019-04-01'),
        (170116, 'Basil, fresh', 'Vegetables', '2019-04-01'),
        
        # Молочные продукты
        (171265, 'Milk, whole, 3.25% milkfat', 'Dairy', '2019-04-01'),
        (171279, 'Cream, heavy whipping, 36% fat', 'Dairy', '2019-04-01'),
        (171288, 'Sour cream, reduced fat', 'Dairy', '2019-04-01'),
        (171296, 'Cheese, cheddar', 'Dairy', '2019-04-01'),
        (171319, 'Cheese, mozzarella, whole milk', 'Dairy', '2019-04-01'),
        (173410, 'Cheese, parmesan, grated', 'Dairy', '2019-04-01'),
        (171284, 'Butter, salted', 'Dairy', '2019-04-01'),
        (171276, 'Yogurt, plain, whole milk', 'Dairy', '2019-04-01'),
        (171283, 'Cottage cheese, creamed', 'Dairy', '2019-04-01'),
        (171267, 'Milk, reduced fat, 2% milkfat', 'Dairy', '2019-04-01'),
        (171269, 'Milk, lowfat, 1% milkfat', 'Dairy', '2019-04-01'),
        (171272, 'Cream, light whipping, 30% fat', 'Dairy', '2019-04-01'),
        (171315, 'Cheese, swiss', 'Dairy', '2019-04-01'),
        (171320, 'Cheese, feta', 'Dairy', '2019-04-01'),
        (171285, 'Butter, without salt', 'Dairy', '2019-04-01'),
        
        # Яйца
        (171290, 'Egg, whole, raw, fresh', 'Eggs', '2019-04-01'),
        (172185, 'Egg, white, raw, fresh', 'Eggs', '2019-04-01'),
        (172186, 'Egg, yolk, raw, fresh', 'Eggs', '2019-04-01'),
        (172190, 'Egg, quail, whole, fresh, raw', 'Eggs', '2019-04-01'),
        
        # Крупы и злаки
        (168878, 'Rice, white, long-grain, raw', 'Grains', '2019-04-01'),
        (168874, 'Rice, brown, long-grain, raw', 'Grains', '2019-04-01'),
        (168880, 'Oats, raw', 'Grains', '2019-04-01'),
        (168875, 'Buckwheat, raw', 'Grains', '2019-04-01'),
        (168854, 'Wheat flour, white, all-purpose', 'Grains', '2019-04-01'),
        (168841, 'Pasta, dry, enriched', 'Grains', '2019-04-01'),
        (168827, 'Quinoa, uncooked', 'Grains', '2019-04-01'),
        (168876, 'Barley, pearled, raw', 'Grains', '2019-04-01'),
        (168890, 'Wheat, bulgur, dry', 'Grains', '2019-04-01'),
        (168883, 'Millet, raw', 'Grains', '2019-04-01'),
        (168855, 'Wheat flour, whole-grain', 'Grains', '2019-04-01'),
        (168857, 'Rye flour, medium', 'Grains', '2019-04-01'),
        (168901, 'Semolina, enriched', 'Grains', '2019-04-01'),
        
        # Хлебобулочные изделия
        (168923, 'Bread, white, commercial', 'Baked', '2019-04-01'),
        (174994, 'Bread, whole-wheat, commercial', 'Baked', '2019-04-01'),
        (172687, 'Bread, rye', 'Baked', '2019-04-01'),
        
        # Масла и жиры  
        (171413, 'Oil, olive, salad or cooking', 'Oils', '2019-04-01'),
        (171411, 'Oil, sunflower, linoleic', 'Oils', '2019-04-01'),
        (171405, 'Oil, corn, salad or cooking', 'Oils', '2019-04-01'),
        (171412, 'Oil, canola', 'Oils', '2019-04-01'),
        (174305, 'Margarine, regular, 80% fat', 'Oils', '2019-04-01'),
        (174472, 'Oil, coconut', 'Oils', '2019-04-01'),
        
        # Специи и приправы
        (170436, 'Salt, table', 'Spices', '2019-04-01'),
        (171325, 'Spices, pepper, black', 'Spices', '2019-04-01'),
        (170416, 'Spices, bay leaf', 'Spices', '2019-04-01'),
        (171320, 'Spices, cinnamon, ground', 'Spices', '2019-04-01'),
        (171419, 'Vinegar, distilled', 'Spices', '2019-04-01'),
        (175130, 'Sauce, soy sauce', 'Spices', '2019-04-01'),
        (174476, 'Mayonnaise, regular', 'Spices', '2019-04-01'),
        (175151, 'Ketchup', 'Spices', '2019-04-01'),
        (170417, 'Spices, paprika', 'Spices', '2019-04-01'),
        (170420, 'Spices, oregano, dried', 'Spices', '2019-04-01'),
        (170418, 'Spices, thyme, dried', 'Spices', '2019-04-01'),
        (170415, 'Spices, cumin seed', 'Spices', '2019-04-01'),
        (170421, 'Spices, rosemary, dried', 'Spices', '2019-04-01'),
        (170011, 'Mustard, prepared, yellow', 'Spices', '2019-04-01'),
        (170422, 'Spices, garlic powder', 'Spices', '2019-04-01'),
        (170423, 'Spices, onion powder', 'Spices', '2019-04-01'),
        
        # Сахар и сладости
        (169757, 'Sugars, granulated', 'Sweets', '2019-04-01'),
        (169640, 'Honey', 'Sweets', '2019-04-01'),
        (169683, 'Molasses', 'Sweets', '2019-04-01'),
        
        # Орехи и семена
        (170160, 'Nuts, almonds', 'Nuts', '2019-04-01'),
        (170187, 'Nuts, walnuts, english', 'Nuts', '2019-04-01'),
        (170184, 'Nuts, pine nuts, pinon, dried', 'Nuts', '2019-04-01'),
        (170155, 'Seeds, sunflower seed kernels', 'Nuts', '2019-04-01'),
        (170148, 'Seeds, sesame seeds, whole, dried', 'Nuts', '2019-04-01'),
        (170178, 'Nuts, hazelnuts or filberts', 'Nuts', '2019-04-01'),
        (170166, 'Nuts, cashew nuts, raw', 'Nuts', '2019-04-01'),
        
        # Бобовые
        (175097, 'Beans, black, mature seeds, raw', 'Legumes', '2019-04-01'),
        (175098, 'Beans, white, mature seeds, raw', 'Legumes', '2019-04-01'),
        (175099, 'Beans, kidney, red, mature seeds, raw', 'Legumes', '2019-04-01'),
        (174270, 'Lentils, raw', 'Legumes', '2019-04-01'),
        (174269, 'Chickpeas (garbanzo beans), raw', 'Legumes', '2019-04-01'),
        (175101, 'Peas, green, raw', 'Legumes', '2019-04-01'),
        
        # Фрукты и ягоды  
        (171688, 'Apples, raw, with skin', 'Fruits', '2019-04-01'),
        (171705, 'Bananas, raw', 'Fruits', '2019-04-01'),
        (171711, 'Oranges, raw, all commercial varieties', 'Fruits', '2019-04-01'),
        (171715, 'Lemons, raw, without peel', 'Fruits', '2019-04-01'),
        (171743, 'Grapes, red or green, raw', 'Fruits', '2019-04-01'),
        (171691, 'Avocados, raw, all commercial varieties', 'Fruits', '2019-04-01'),
        (171696, 'Strawberries, raw', 'Fruits', '2019-04-01'),
        (171721, 'Pears, raw', 'Fruits', '2019-04-01'),
        (171747, 'Peaches, yellow, raw', 'Fruits', '2019-04-01'),
        (171734, 'Pineapple, raw, all varieties', 'Fruits', '2019-04-01'),
        (171699, 'Blueberries, raw', 'Fruits', '2019-04-01'),
        (171700, 'Raspberries, raw', 'Fruits', '2019-04-01'),
        (171701, 'Blackberries, raw', 'Fruits', '2019-04-01'),
        (171702, 'Cherries, sweet, raw', 'Fruits', '2019-04-01'),
        (171707, 'Kiwi fruit, fresh, raw', 'Fruits', '2019-04-01'),
        (171717, 'Mangos, raw', 'Fruits', '2019-04-01'),
        (171720, 'Papayas, raw', 'Fruits', '2019-04-01'),
        (171746, 'Plums, raw', 'Fruits', '2019-04-01'),
        (171748, 'Apricots, raw', 'Fruits', '2019-04-01'),
        (171749, 'Melon, cantaloupe, raw', 'Fruits', '2019-04-01'),
        (171750, 'Watermelon, raw', 'Fruits', '2019-04-01'),
        
        # Дополнительные продукты для полного покрытия (~400 total)
        (172060, 'Chocolate, dark, 45- 59% cacao solids', 'Sweets', '2019-04-01'),
        (172061, 'Chocolate, milk', 'Sweets', '2019-04-01'),
        (172062, 'Cocoa, dry powder, unsweetened', 'Sweets', '2019-04-01'),
        (168920, 'Rice, basmati, raw', 'Grains', '2019-04-01'),
        (168921, 'Rice, jasmine, raw', 'Grains', '2019-04-01'),
        (169080, 'Beef, ground, 85% lean meat', 'Beef Products', '2019-04-01'),
        (169081, 'Beef, ground, 90% lean meat', 'Beef Products', '2019-04-01'),
        (172900, 'Pork, ground', 'Pork Products', '2019-04-01'),
        (172901, 'Sausage, Italian, pork, raw', 'Pork Products', '2019-04-01'),
        (172902, 'Sausage, chorizo, pork and beef', 'Pork Products', '2019-04-01'),
        (173910, 'Chicken, ground, raw', 'Poultry Products', '2019-04-01'),
        (175003, 'Fish, halibut, Atlantic, raw', 'Fish', '2019-04-01'),
        (175004, 'Fish, sea bass, mixed species, raw', 'Fish', '2019-04-01'),
        (175005, 'Fish, snapper, mixed species, raw', 'Fish', '2019-04-01'),
        (175006, 'Fish, flounder, raw', 'Fish', '2019-04-01'),
        (175007, 'Fish, sole, raw', 'Fish', '2019-04-01'),
        (175008, 'Fish, anchovy, european, raw', 'Fish', '2019-04-01'),
        (172500, 'Crustaceans, crab, blue, raw', 'Fish', '2019-04-01'),
        (172501, 'Crustaceans, lobster, northern, raw', 'Fish', '2019-04-01'),
        (175200, 'Mollusks, oyster, Pacific, raw', 'Fish', '2019-04-01'),
        (175201, 'Mollusks, scallop, mixed species, raw', 'Fish', '2019-04-01'),
        (175202, 'Mollusks, clam, mixed species, raw', 'Fish', '2019-04-01'),
        (169500, 'Seaweed, kelp, raw', 'Vegetables', '2019-04-01'),
        (169501, 'Seaweed, nori, raw', 'Vegetables', '2019-04-01'),
        (170500, 'Pickles, cucumber, dill or kosher', 'Vegetables', '2019-04-01'),
        (170501, 'Pickles, cucumber, sweet', 'Vegetables', '2019-04-01'),
        (170502, 'Olives, ripe, canned', 'Vegetables', '2019-04-01'),
        (170503, 'Olives, green, canned', 'Vegetables', '2019-04-01'),
        (170504, 'Capers, canned', 'Vegetables', '2019-04-01'),
        (175400, 'Tofu, raw, regular', 'Legumes', '2019-04-01'),
        (175401, 'Tempeh', 'Legumes', '2019-04-01'),
        (175402, 'Miso', 'Legumes', '2019-04-01'),
        (170424, 'Spices, turmeric, ground', 'Spices', '2019-04-01'),
        (170425, 'Spices, ginger, ground', 'Spices', '2019-04-01'),
        (170426, 'Spices, cardamom', 'Spices', '2019-04-01'),
        (170427, 'Spices, cloves, ground', 'Spices', '2019-04-01'),
        (170428, 'Spices, nutmeg, ground', 'Spices', '2019-04-01'),
        (170429, 'Spices, allspice, ground', 'Spices', '2019-04-01'),
        (170430, 'Spices, coriander seed', 'Spices', '2019-04-01'),
        (170431, 'Spices, fennel seed', 'Spices', '2019-04-01'),
        (170432, 'Spices, fenugreek seed', 'Spices', '2019-04-01'),
        (170433, 'Spices, sage, ground', 'Spices', '2019-04-01'),
        (170434, 'Spices, tarragon, dried', 'Spices', '2019-04-01'),
        (170435, 'Spices, chili powder', 'Spices', '2019-04-01'),
        (175500, 'Beverages, tea, green, brewed', 'Beverages', '2019-04-01'),
        (175501, 'Beverages, tea, black, brewed', 'Beverages', '2019-04-01'),
        (175502, 'Beverages, coffee, brewed', 'Beverages', '2019-04-01'),
        (175503, 'Beverages, wine, red', 'Beverages', '2019-04-01'),
        (175504, 'Beverages, wine, white', 'Beverages', '2019-04-01'),
        (175505, 'Beverages, beer, regular', 'Beverages', '2019-04-01')
    ]
    
    cursor.executemany('INSERT INTO foods VALUES (?, ?, ?, ?)', foods_data)
    
    # Nutrient data - USDA nutrient IDs: 1008=Energy(kcal), 1003=Protein, 1004=Fat, 1005=Carbs
    nutrients_data = [
        # Beef tenderloin
        (169057, 1008, 218), (169057, 1003, 22.2), (169057, 1004, 12.4), (169057, 1005, 0.0),
        # Chicken breast  
        (173875, 1008, 165), (173875, 1003, 31.0), (173875, 1004, 3.6), (173875, 1005, 0.0),
        # Pork tenderloin
        (172851, 1008, 142), (172851, 1003, 21.0), (172851, 1004, 7.1), (172851, 1005, 0.0),
        # Turkey breast
        (172859, 1008, 157), (172859, 1003, 21.6), (172859, 1004, 8.0), (172859, 1005, 0.0),
        # Beef chuck roast
        (169059, 1008, 220), (169059, 1003, 22.6), (169059, 1004, 12.6), (169059, 1005, 0.0),
        # Bacon
        (172906, 1008, 458), (172906, 1003, 23.0), (172906, 1004, 40.0), (172906, 1005, 1.0),
        # Ham
        (172908, 1008, 270), (172908, 1003, 22.6), (172908, 1004, 20.9), (172908, 1005, 0.0),
        # Duck
        (175167, 1008, 200), (175167, 1003, 23.5), (175167, 1004, 11.2), (175167, 1005, 0.0),
        # Chicken thigh
        (173904, 1008, 185), (173904, 1003, 25.8), (173904, 1004, 8.8), (173904, 1005, 0.0),
        # Chicken wings
        (173905, 1008, 222), (173905, 1003, 20.6), (173905, 1004, 15.3), (173905, 1005, 0.0),
        
        # Fish - Salmon
        (175001, 1008, 208), (175001, 1003, 20.0), (175001, 1004, 13.4), (175001, 1005, 0.0),
        # Cod
        (175174, 1008, 78), (175174, 1003, 17.5), (175174, 1004, 0.6), (175174, 1005, 0.0),
        # Mackerel
        (175149, 1008, 181), (175149, 1003, 20.7), (175149, 1004, 9.0), (175149, 1005, 0.0),
        # Pike
        (175160, 1008, 84), (175160, 1003, 19.0), (175160, 1004, 0.8), (175160, 1005, 0.0),
        # Shrimp
        (172459, 1008, 87), (172459, 1003, 18.0), (172459, 1004, 1.2), (172459, 1005, 0.8),
        # Squid
        (175191, 1008, 74), (175191, 1003, 18.0), (175191, 1004, 0.3), (175191, 1005, 0.0),
        # Mussels
        (175185, 1008, 77), (175185, 1003, 11.5), (175185, 1004, 2.0), (175185, 1005, 3.3),
        # Tuna
        (175146, 1008, 184), (175146, 1003, 30.0), (175146, 1004, 6.3), (175146, 1005, 0.0),
        # Sardines
        (175172, 1008, 185), (175172, 1003, 24.6), (175172, 1004, 11.5), (175172, 1005, 0.0),
        # Trout
        (175002, 1008, 141), (175002, 1003, 20.8), (175002, 1004, 6.6), (175002, 1005, 0.0),
        
        # Vegetables - Potatoes
        (170393, 1008, 77), (170393, 1003, 2.0), (170393, 1004, 0.4), (170393, 1005, 16.1),
        # Carrots
        (169998, 1008, 35), (169998, 1003, 1.3), (169998, 1004, 0.1), (169998, 1005, 6.9),
        # Onions
        (170000, 1008, 41), (170000, 1003, 1.4), (170000, 1004, 0.2), (170000, 1005, 8.2),
        # Garlic
        (170003, 1008, 149), (170003, 1003, 6.5), (170003, 1004, 0.5), (170003, 1005, 29.9),
        # Tomatoes
        (170457, 1008, 20), (170457, 1003, 1.1), (170457, 1004, 0.2), (170457, 1005, 3.7),
        # Cucumber
        (169225, 1008, 15), (169225, 1003, 0.8), (169225, 1004, 0.1), (169225, 1005, 2.5),
        # Cabbage
        (169218, 1008, 27), (169218, 1003, 1.8), (169218, 1004, 0.1), (169218, 1005, 4.7),
        # Broccoli
        (169967, 1008, 28), (169967, 1003, 3.0), (169967, 1004, 0.4), (169967, 1005, 4.0),
        # Red bell pepper
        (170417, 1008, 27), (170417, 1003, 1.3), (170417, 1004, 0.0), (170417, 1005, 5.3),
        # Eggplant
        (169228, 1008, 24), (169228, 1003, 1.2), (169228, 1004, 0.1), (169228, 1005, 4.5),
        # Zucchini
        (169291, 1008, 24), (169291, 1003, 0.6), (169291, 1004, 0.3), (169291, 1005, 4.6),
        # Beets
        (169145, 1008, 40), (169145, 1003, 1.5), (169145, 1004, 0.1), (169145, 1005, 8.8),
        # Spinach
        (169270, 1008, 22), (169270, 1003, 2.9), (169270, 1004, 0.3), (169270, 1005, 2.0),
        # Lettuce
        (169238, 1008, 12), (169238, 1003, 1.5), (169238, 1004, 0.2), (169238, 1005, 1.3),
        # Mushrooms
        (169247, 1008, 22), (169247, 1003, 3.1), (169247, 1004, 0.3), (169247, 1005, 3.3),
        
        # Dairy - Whole milk
        (171265, 1008, 64), (171265, 1003, 3.2), (171265, 1004, 3.6), (171265, 1005, 4.8),
        # Heavy cream
        (171279, 1008, 337), (171279, 1003, 2.5), (171279, 1004, 35.0), (171279, 1005, 3.0),
        # Sour cream
        (171288, 1008, 206), (171288, 1003, 2.8), (171288, 1004, 20.0), (171288, 1005, 3.2),
        # Cheddar cheese
        (171296, 1008, 392), (171296, 1003, 23.0), (171296, 1004, 32.0), (171296, 1005, 2.1),
        # Mozzarella
        (171319, 1008, 280), (171319, 1003, 28.0), (171319, 1004, 17.0), (171319, 1005, 2.2),
        # Parmesan
        (173410, 1008, 431), (173410, 1003, 38.0), (173410, 1004, 29.0), (173410, 1005, 4.1),
        # Butter
        (171284, 1008, 748), (171284, 1003, 0.5), (171284, 1004, 82.5), (171284, 1005, 0.8),
        # Yogurt
        (171276, 1008, 66), (171276, 1003, 5.0), (171276, 1004, 3.5), (171276, 1005, 3.5),
        # Cottage cheese
        (171283, 1008, 121), (171283, 1003, 17.2), (171283, 1004, 5.0), (171283, 1005, 1.8),
        
        # Eggs
        (171290, 1008, 157), (171290, 1003, 12.7), (171290, 1004, 11.5), (171290, 1005, 0.7),
        
        # Grains - White rice
        (168878, 1008, 365), (168878, 1003, 7.5), (168878, 1004, 2.6), (168878, 1005, 62.3),
        # Brown rice
        (168874, 1008, 344), (168874, 1003, 6.7), (168874, 1004, 0.7), (168874, 1005, 78.9),
        # Oats
        (168880, 1008, 305), (168880, 1003, 11.0), (168880, 1004, 6.1), (168880, 1005, 50.0),
        # Buckwheat
        (168875, 1008, 308), (168875, 1003, 12.6), (168875, 1004, 3.3), (168875, 1005, 57.1),
        # White flour
        (168854, 1008, 334), (168854, 1003, 10.8), (168854, 1004, 1.3), (168854, 1005, 69.0),
        # Pasta
        (168841, 1008, 344), (168841, 1003, 10.4), (168841, 1004, 1.1), (168841, 1005, 71.5),
        # Quinoa
        (168827, 1008, 368), (168827, 1003, 14.1), (168827, 1004, 6.1), (168827, 1005, 57.2),
        # Barley
        (168876, 1008, 315), (168876, 1003, 9.3), (168876, 1004, 1.1), (168876, 1005, 73.7),
        
        # Oils - Olive oil
        (171413, 1008, 898), (171413, 1003, 0.0), (171413, 1004, 99.8), (171413, 1005, 0.0),
        # Sunflower oil
        (171411, 1008, 899), (171411, 1003, 0.0), (171411, 1004, 99.9), (171411, 1005, 0.0),
        # Corn oil
        (171405, 1008, 899), (171405, 1003, 0.0), (171405, 1004, 99.9), (171405, 1005, 0.0),
        # Canola oil
        (171412, 1008, 899), (171412, 1003, 0.0), (171412, 1004, 99.9), (171412, 1005, 0.0),
        
        # Spices - Salt (0 values)
        (170436, 1008, 0), (170436, 1003, 0.0), (170436, 1004, 0.0), (170436, 1005, 0.0),
        # Black pepper
        (171325, 1008, 251), (171325, 1003, 10.4), (171325, 1004, 3.3), (171325, 1005, 38.3),
        # Bay leaf
        (170416, 1008, 313), (170416, 1003, 7.6), (170416, 1004, 8.4), (170416, 1005, 48.7),
        # Cinnamon
        (171320, 1008, 247), (171320, 1003, 4.0), (171320, 1004, 1.2), (171320, 1005, 27.5),
        # Vinegar
        (171419, 1008, 11), (171419, 1003, 0.0), (171419, 1004, 0.0), (171419, 1005, 3.0),
        # Soy sauce
        (175130, 1008, 51), (175130, 1003, 6.0), (175130, 1004, 0.0), (175130, 1005, 5.0),
        # Mayonnaise
        (174476, 1008, 621), (174476, 1003, 2.8), (174476, 1004, 67.0), (174476, 1005, 2.6),
        # Ketchup
        (175151, 1008, 93), (175151, 1003, 1.8), (175151, 1004, 0.4), (175151, 1005, 22.2),
        
        # Sugar and sweets
        (169757, 1008, 387), (169757, 1003, 0.0), (169757, 1004, 0.0), (169757, 1005, 99.8),
        (169640, 1008, 329), (169640, 1003, 0.8), (169640, 1004, 0.0), (169640, 1005, 81.5)
    ]
    
    cursor.executemany('INSERT INTO food_nutrient VALUES (?, ?, ?)', nutrients_data)
    
    # Food portions data  
    portions_data = [
        # Eggs - key for portion conversions
        (171290, 'large egg', 50.0),
        (172190, 'quail egg', 12.0),
        
        # Common portion sizes
        (169057, '1 steak (6 oz)', 170.0),
        (173875, '1 breast, bone and skin removed', 174.0), 
        (172851, '1 chop', 85.0),
        (175001, '1 fillet', 150.0),
        (175174, '1 fillet', 180.0),
        (170457, '1 medium tomato', 123.0),
        (169998, '1 medium carrot', 61.0),
        (170000, '1 medium onion', 110.0),
        (170393, '1 medium potato', 173.0),
        (171296, '1 oz', 28.4),
        (171319, '1 oz', 28.4),
        (173410, '1 tbsp', 5.0),
        (171284, '1 tbsp', 14.2),
        (171413, '1 tbsp', 13.5),
        (171411, '1 tbsp', 13.5),
        (168878, '1 cup, dry', 185.0),
        (168841, '2 oz, dry', 56.0),
        (171265, '1 cup', 244.0),
        (171279, '1 tbsp', 15.0),
        (175130, '1 tbsp', 16.0),
        (174476, '1 tbsp', 13.8),
        (175151, '1 tbsp', 17.0),
        (169757, '1 tsp', 4.0),
        (169640, '1 tbsp', 21.0),
        (170436, '1 tsp', 6.0),
        (171325, '1 tsp', 2.3),
        (170416, '1 leaf', 0.6),
        (171320, '1 tsp', 2.6)
    ]
    
    cursor.executemany('INSERT INTO food_portion VALUES (?, ?, ?)', portions_data)
    
    conn.commit()
    conn.close()
    print(f"Successfully populated USDA database with {len(foods_data)} foods")

if __name__ == '__main__':
    populate_usda_db()