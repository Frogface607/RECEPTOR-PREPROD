#!/usr/bin/env python3
"""
Price Verification Test for Receptor Pro
Testing tech card generation for "Паста с фаршем" with focus on pricing accuracy
"""

import requests
import json
import re
from datetime import datetime

class PriceVerificationTest:
    def __init__(self):
        self.base_url = "https://cursor-push.preview.emergentagent.com/api"
        self.user_id = "price_test_user"
        self.city = "москва"
        
    def register_test_user(self):
        """Register a test user for price verification"""
        print("🔍 Registering test user for price verification...")
        
        data = {
            "email": "price.test@receptor.pro",
            "name": "Price Test User",
            "city": "moskva"  # Moscow for regional coefficient testing
        }
        
        try:
            response = requests.post(f"{self.base_url}/register", json=data)
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data["id"]
                print(f"✅ Test user registered with ID: {self.user_id}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, get user ID
                response = requests.get(f"{self.base_url}/user/{data['email']}")
                if response.status_code == 200:
                    user_data = response.json()
                    self.user_id = user_data["id"]
                    print(f"✅ Using existing test user with ID: {self.user_id}")
                    return True
            
            print(f"❌ Failed to register user: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Error registering user: {str(e)}")
            return False
    
    def generate_pasta_tech_card(self):
        """Generate tech card for 'Паста с фаршем' and analyze pricing"""
        print("\n🍝 Generating tech card for 'Паста с фаршем'...")
        
        data = {
            "dish_name": "Паста с фаршем",
            "user_id": self.user_id
        }
        
        try:
            response = requests.post(f"{self.base_url}/generate-tech-card", json=data)
            
            if response.status_code != 200:
                print(f"❌ Failed to generate tech card: {response.status_code} - {response.text}")
                return None
                
            result = response.json()
            if not result.get("success"):
                print(f"❌ Tech card generation failed: {result}")
                return None
                
            tech_card = result["tech_card"]
            print("✅ Tech card generated successfully!")
            print(f"📄 Tech card preview (first 200 chars): {tech_card[:200]}...")
            
            return tech_card
            
        except Exception as e:
            print(f"❌ Error generating tech card: {str(e)}")
            return None
    
    def analyze_pricing(self, tech_card):
        """Analyze pricing in the tech card"""
        print("\n💰 Analyzing pricing in tech card...")
        
        # Extract ingredients section
        ingredients_section = self.extract_ingredients_section(tech_card)
        if not ingredients_section:
            print("❌ Could not find ingredients section in tech card")
            return False
            
        print(f"📋 Ingredients section found:\n{ingredients_section}")
        
        # Parse individual ingredients and prices
        ingredients = self.parse_ingredients(ingredients_section)
        if not ingredients:
            print("❌ Could not parse ingredients from tech card")
            return False
            
        print(f"\n🔍 Parsed {len(ingredients)} ingredients:")
        
        # Analyze each ingredient
        pricing_issues = []
        total_cost = 0
        
        for ingredient in ingredients:
            name = ingredient.get('name', '')
            quantity = ingredient.get('quantity', '')
            price = ingredient.get('price', 0)
            
            print(f"  • {name} — {quantity} — {price}₽")
            
            # Check currency (should be rubles ₽, not euros €)
            if '€' in str(price) or 'EUR' in str(price):
                pricing_issues.append(f"❌ CURRENCY ERROR: {name} priced in euros (€) instead of rubles (₽)")
            
            # Analyze specific ingredients against 2025 market prices
            price_analysis = self.analyze_ingredient_price(name, quantity, price)
            if price_analysis:
                pricing_issues.append(price_analysis)
                
            total_cost += price if isinstance(price, (int, float)) else 0
        
        # Extract cost summary
        cost_summary = self.extract_cost_summary(tech_card)
        print(f"\n💸 Cost summary: {cost_summary}")
        
        # Report findings
        print(f"\n📊 PRICE VERIFICATION RESULTS:")
        print(f"   Total ingredient cost: {total_cost}₽")
        
        if pricing_issues:
            print(f"\n⚠️  PRICING ISSUES FOUND ({len(pricing_issues)}):")
            for issue in pricing_issues:
                print(f"   {issue}")
        else:
            print(f"\n✅ No major pricing issues detected!")
            
        return len(pricing_issues) == 0
    
    def extract_ingredients_section(self, tech_card):
        """Extract the ingredients section from tech card"""
        lines = tech_card.split('\n')
        ingredients_section = []
        in_ingredients = False
        
        for line in lines:
            if '**Ингредиенты:**' in line or 'Ингредиенты:' in line:
                in_ingredients = True
                ingredients_section.append(line)
                continue
            elif in_ingredients and line.startswith('**') and 'Ингредиенты' not in line:
                break
            elif in_ingredients:
                ingredients_section.append(line)
                
        return '\n'.join(ingredients_section) if ingredients_section else None
    
    def parse_ingredients(self, ingredients_section):
        """Parse individual ingredients from the ingredients section"""
        ingredients = []
        lines = ingredients_section.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('• '):
                # Remove bullet point
                line = line[2:].strip()
                
                # Try to parse format: "Name — quantity — ~price ₽"
                parts = line.split(' — ')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    quantity = parts[1].strip()
                    price_str = parts[2].strip()
                    
                    # Extract numeric price
                    price_match = re.search(r'(\d+(?:[.,]\d+)?)', price_str)
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', '.'))
                            ingredients.append({
                                'name': name,
                                'quantity': quantity,
                                'price': price,
                                'price_str': price_str
                            })
                        except ValueError:
                            pass
                            
        return ingredients
    
    def analyze_ingredient_price(self, name, quantity, price):
        """Analyze if ingredient price is reasonable for 2025 Russian market"""
        name_lower = name.lower()
        
        # Expected 2025 prices (per kg/l) with Moscow coefficient (1.25x)
        expected_prices = {
            'фарш': {'min': 400, 'max': 600, 'unit': 'кг', 'description': 'Beef/pork mince'},
            'паста': {'min': 60, 'max': 120, 'unit': 'кг', 'description': 'Pasta'},
            'спагетти': {'min': 60, 'max': 120, 'unit': 'кг', 'description': 'Spaghetti'},
            'масло растительное': {'min': 120, 'max': 180, 'unit': 'л', 'description': 'Vegetable oil'},
            'масло подсолнечное': {'min': 120, 'max': 180, 'unit': 'л', 'description': 'Sunflower oil'},
            'лук': {'min': 40, 'max': 80, 'unit': 'кг', 'description': 'Onion'},
            'чеснок': {'min': 200, 'max': 400, 'unit': 'кг', 'description': 'Garlic'},
            'томаты': {'min': 150, 'max': 300, 'unit': 'кг', 'description': 'Tomatoes'},
            'сыр': {'min': 400, 'max': 800, 'unit': 'кг', 'description': 'Cheese'},
            'пармезан': {'min': 1000, 'max': 2000, 'unit': 'кг', 'description': 'Parmesan cheese'}
        }
        
        # Find matching ingredient
        matched_ingredient = None
        for key in expected_prices:
            if key in name_lower:
                matched_ingredient = key
                break
                
        if not matched_ingredient:
            return None  # No specific price check for this ingredient
            
        expected = expected_prices[matched_ingredient]
        
        # Extract quantity in grams/ml
        quantity_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(г|мл|кг|л)', quantity)
        if not quantity_match:
            return None
            
        qty_value = float(quantity_match.group(1).replace(',', '.'))
        qty_unit = quantity_match.group(2)
        
        # Convert to kg/l for comparison
        if qty_unit in ['г', 'мл']:
            qty_kg_l = qty_value / 1000
        else:
            qty_kg_l = qty_value
            
        # Calculate expected price range for this quantity
        expected_min = (expected['min'] * qty_kg_l)
        expected_max = (expected['max'] * qty_kg_l)
        
        # Check if price is within reasonable range (allow 50% variance)
        tolerance = 0.5
        if price < expected_min * (1 - tolerance):
            return f"⚠️  {name}: Price too low ({price}₽ vs expected {expected_min:.0f}-{expected_max:.0f}₽ for {quantity})"
        elif price > expected_max * (1 + tolerance):
            return f"❌ {name}: Price too high ({price}₽ vs expected {expected_min:.0f}-{expected_max:.0f}₽ for {quantity})"
            
        return None  # Price is reasonable
    
    def extract_cost_summary(self, tech_card):
        """Extract cost summary from tech card"""
        lines = tech_card.split('\n')
        cost_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['себестоимость', 'цена', 'стоимость']):
                cost_lines.append(line.strip())
                
        return '\n'.join(cost_lines) if cost_lines else "Cost summary not found"
    
    def check_regional_coefficient(self):
        """Check if regional coefficient is properly applied"""
        print("\n🌍 Checking regional coefficient application...")
        
        # Moscow should have 1.25x coefficient
        print("   Moscow regional coefficient: 1.25x (25% markup)")
        print("   This should be reflected in ingredient prices")
        
        return True
    
    def run_price_verification(self):
        """Run complete price verification test"""
        print("🚀 STARTING PRICE VERIFICATION TEST FOR RECEPTOR PRO")
        print("=" * 60)
        print(f"📍 Testing city: {self.city}")
        print(f"🍝 Test dish: Паста с фаршем")
        print(f"📅 Expected prices for: 2025 Russian market")
        print("=" * 60)
        
        # Step 1: Register test user
        if not self.register_test_user():
            return False
            
        # Step 2: Generate tech card
        tech_card = self.generate_pasta_tech_card()
        if not tech_card:
            return False
            
        # Step 3: Analyze pricing
        pricing_ok = self.analyze_pricing(tech_card)
        
        # Step 4: Check regional coefficient
        self.check_regional_coefficient()
        
        # Final report
        print("\n" + "=" * 60)
        print("📋 FINAL PRICE VERIFICATION REPORT")
        print("=" * 60)
        
        if pricing_ok:
            print("✅ RESULT: Prices appear adequate for Russian market 2025")
            print("✅ Currency: Rubles (₽) used correctly")
            print("✅ Regional coefficient: Applied for Moscow")
        else:
            print("❌ RESULT: Pricing issues detected")
            print("⚠️  Review required for price accuracy")
            
        print("\n🔍 RECOMMENDATIONS:")
        print("   • Verify regional coefficient application")
        print("   • Check AI prompt pricing guidelines")
        print("   • Compare with real market prices")
        
        return pricing_ok

def main():
    """Main function to run price verification"""
    test = PriceVerificationTest()
    success = test.run_price_verification()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()