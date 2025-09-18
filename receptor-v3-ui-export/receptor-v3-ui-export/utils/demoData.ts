import { TechCardV2 } from '../types/techcard-v2'

// Demo tech card data for fallback scenarios (HOTFIX: normalized for component compatibility)
export const DEMO_TECH_CARDS: Record<string, TechCardV2> = {
  'паста карбонара': {
    id: 'demo-pasta-carbonara',
    title: 'Паста Карбонара',
    description: 'Классическая итальянская паста с беконом и яйцом',
    category: 'основное блюдо',
    status: 'READY',
    portions: 1,
    ingredients: [
      {
        name: 'Спагетти',
        brutto: 100,
        netto: 100,
        unit: 'г',
        loss_pct: 0
      },
      {
        name: 'Бекон',
        brutto: 50,
        netto: 50,
        unit: 'г',
        loss_pct: 0
      },
      {
        name: 'Яйца куриные',
        brutto: 60,
        netto: 60,
        unit: 'г',
        loss_pct: 0
      },
      {
        name: 'Пармезан тертый',
        brutto: 30,
        netto: 30,
        unit: 'г',
        loss_pct: 0
      }
    ],
    process_steps: [
      {
        title: 'Подготовка ингредиентов',
        description: 'Нарезать бекон, натереть сыр, взбить яйца',
        duration_min: 10
      },
      {
        title: 'Варка пасты',
        description: 'Отварить спагетти в подсоленной воде до состояния аль денте',
        duration_min: 12
      },
      {
        title: 'Приготовление соуса',
        description: 'Обжарить бекон, смешать с яйцами и сыром',
        duration_min: 8
      }
    ],
    nutrition: {
      calories_per_100g: 310,
      proteins_per_100g: 15.2,
      fats_per_100g: 12.1,
      carbs_per_100g: 35.8,
      total_calories: 868,
      total_proteins: 42.6,
      total_fats: 33.9,
      total_carbs: 100.2
    },
    cost: {
      total_cost: 185,
      cost_per_portion: 185,
      currency: 'RUB'
    },
    yield: {
      total: 280,
      per_portion: 280,
      unit: 'г'
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  'борщ украинский': {
    id: 'demo-borscht-ukrainian',
    title: 'Борщ украинский',
    description: 'Традиционный украинский борщ с говядиной',
    category: 'суп',
    status: 'READY',  
    portions: 1,
    ingredients: [
      {
        name: 'Говядина',
        brutto: 120,
        netto: 100,
        unit: 'г',
        loss_pct: 16.7
      },
      {
        name: 'Свекла',
        brutto: 80,
        netto: 72,
        unit: 'г',
        loss_pct: 10
      },
      {
        name: 'Капуста белокочанная',
        brutto: 70,
        netto: 63,
        unit: 'г',
        loss_pct: 10
      },
      {
        name: 'Морковь',
        brutto: 35,
        netto: 30,
        unit: 'г',
        loss_pct: 14.3
      }
    ],
    process_steps: [
      {
        title: 'Варка бульона',
        description: 'Отварить говядину до готовности в подсоленной воде',
        duration_min: 90
      },
      {
        title: 'Подготовка овощей',
        description: 'Нарезать все овощи, свеклу натереть на терке',
        duration_min: 15
      },
      {
        title: 'Варка борща',
        description: 'Добавить овощи в бульон и варить до готовности',
        duration_min: 30
      }
    ],
    nutrition: {
      calories_per_100g: 95,
      proteins_per_100g: 8.2,
      fats_per_100g: 4.1,
      carbs_per_100g: 7.8,
      total_calories: 285,
      total_proteins: 24.6,
      total_fats: 12.3,
      total_carbs: 23.4
    },
    cost: {
      total_cost: 145,
      cost_per_portion: 145,
      currency: 'RUB'
    },
    yield: {
      total: 300,
      per_portion: 300,
      unit: 'г'
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

// Get demo tech card by dish name
export const getDemoTechCard = (dishName: string): TechCardV2 | null => {
  const normalizedName = dishName.toLowerCase().trim()
  
  // Try exact match first
  if (DEMO_TECH_CARDS[normalizedName]) {
    return DEMO_TECH_CARDS[normalizedName]
  }
  
  // Try partial matches
  for (const [key, card] of Object.entries(DEMO_TECH_CARDS)) {
    if (normalizedName.includes(key) || key.includes(normalizedName)) {
      return card
    }
  }
  
  // Default fallback - return pasta carbonara
  return DEMO_TECH_CARDS['паста карбонара']
}

// Check if dish name should use demo data
export const shouldUseDemoData = (dishName: string): boolean => {
  const demoKeywords = ['паста', 'карбонара', 'борщ', 'украинский', 'тест', 'demo']
  const normalizedName = dishName.toLowerCase()
  
  return demoKeywords.some(keyword => normalizedName.includes(keyword))
}