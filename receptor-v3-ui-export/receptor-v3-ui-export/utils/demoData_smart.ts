import { TechCardV2 } from '../types/techcard-v2'

// Smart demo data generation based on dish name
export const generateSmartDemoTechCard = (dishName: string): TechCardV2 => {
  const normalizedName = dishName.toLowerCase().trim()
  
  // Simple hash function for consistent random values
  const hashString = (str: string): number => {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32-bit integer
    }
    return Math.abs(hash)
  }
  
  const hash = hashString(normalizedName)
  
  // Generate consistent but varied values based on dish name
  const baseCalories = 120 + (hash % 300) // 120-420 kcal
  const baseProtein = 5 + (hash % 15) // 5-20g protein
  const baseFat = 3 + (hash % 12) // 3-15g fat
  const baseCarbs = 10 + (hash % 40) // 10-50g carbs
  const baseCost = 45 + (hash % 155) // 45-200 rubles
  
  // Generate smart ingredients based on dish name patterns
  const getSmartIngredients = () => {
    const commonIngredients = [
      { name: 'Соль', brutto: 2, netto: 2, unit: 'г', loss_pct: 0 },
      { name: 'Перец черный молотый', brutto: 1, netto: 1, unit: 'г', loss_pct: 0 }
    ]
    
    // Dish-specific ingredients based on keywords
    if (normalizedName.includes('борщ') || normalizedName.includes('суп')) {
      return [
        { name: 'Свекла', brutto: 100, netto: 85, unit: 'г', loss_pct: 15 },
        { name: 'Капуста белокочанная', brutto: 80, netto: 70, unit: 'г', loss_pct: 12 },
        { name: 'Морковь', brutto: 50, netto: 40, unit: 'г', loss_pct: 20 },
        { name: 'Лук репчатый', brutto: 40, netto: 35, unit: 'г', loss_pct: 12 },
        { name: 'Картофель', brutto: 120, netto: 100, unit: 'г', loss_pct: 16 },
        ...commonIngredients
      ]
    }
    
    if (normalizedName.includes('паста') || normalizedName.includes('спагетти')) {
      return [
        { name: 'Спагетти', brutto: 100, netto: 100, unit: 'г', loss_pct: 0 },
        { name: 'Томаты в собственном соку', brutto: 150, netto: 150, unit: 'г', loss_pct: 0 },
        { name: 'Лук репчатый', brutto: 30, netto: 25, unit: 'г', loss_pct: 16 },
        { name: 'Чеснок', brutto: 5, netto: 4, unit: 'г', loss_pct: 20 },
        { name: 'Масло оливковое', brutto: 15, netto: 15, unit: 'мл', loss_pct: 0 },
        ...commonIngredients
      ]
    }
    
    if (normalizedName.includes('салат')) {
      return [
        { name: 'Листья салата', brutto: 50, netto: 45, unit: 'г', loss_pct: 10 },
        { name: 'Помидоры', brutto: 100, netto: 90, unit: 'г', loss_pct: 10 },
        { name: 'Огурцы', brutto: 80, netto: 75, unit: 'г', loss_pct: 6 },
        { name: 'Масло растительное', brutto: 10, netto: 10, unit: 'мл', loss_pct: 0 },
        ...commonIngredients
      ]
    }
    
    if (normalizedName.includes('омлет') || normalizedName.includes('яич')) {
      return [
        { name: 'Яйца куриные', brutto: 120, netto: 120, unit: 'г', loss_pct: 0 },
        { name: 'Молоко', brutto: 50, netto: 50, unit: 'мл', loss_pct: 0 },
        { name: 'Масло сливочное', brutto: 10, netto: 10, unit: 'г', loss_pct: 0 },
        ...commonIngredients
      ]
    }
    
    // Default ingredients for unknown dishes
    return [
      { name: 'Основной ингредиент', brutto: 150, netto: 130, unit: 'г', loss_pct: 13 },
      { name: 'Дополнительный ингредиент', brutto: 80, netto: 70, unit: 'г', loss_pct: 12 },
      { name: 'Специи и приправы', brutto: 5, netto: 5, unit: 'г', loss_pct: 0 },
      ...commonIngredients
    ]
  }
  
  // Generate smart process steps
  const getSmartProcessSteps = () => {
    const steps = []
    
    if (normalizedName.includes('борщ') || normalizedName.includes('суп')) {
      steps.push(
        { title: 'Подготовка овощей', description: 'Очистить и нарезать все овощи', duration_min: 15 },
        { title: 'Приготовление бульона', description: 'Варить основу бульона 30-40 минут', duration_min: 35 },
        { title: 'Добавление овощей', description: 'Поочередно добавить овощи по времени варки', duration_min: 20 },
        { title: 'Финальная варка', description: 'Довести до готовности, приправить', duration_min: 10 }
      )
    } else if (normalizedName.includes('паста')) {
      steps.push(
        { title: 'Подготовка соуса', description: 'Приготовить соус для пасты', duration_min: 10 },
        { title: 'Варка пасты', description: 'Отварить пасту до состояния аль денте', duration_min: 12 },
        { title: 'Соединение', description: 'Соединить пасту с соусом', duration_min: 3 }
      )
    } else if (normalizedName.includes('салат')) {
      steps.push(
        { title: 'Подготовка ингредиентов', description: 'Вымыть и нарезать все овощи', duration_min: 10 },
        { title: 'Смешивание', description: 'Смешать ингредиенты с заправкой', duration_min: 5 }
      )
    } else {
      steps.push(
        { title: 'Подготовка', description: `Подготовить ингредиенты для ${dishName}`, duration_min: 10 },
        { title: 'Основное приготовление', description: `Приготовить ${dishName} согласно технологии`, duration_min: 20 },
        { title: 'Финализация', description: 'Довести до готовности и подать', duration_min: 5 }
      )
    }
    
    return steps
  }
  
  const ingredients = getSmartIngredients()
  const processSteps = getSmartProcessSteps()
  
  return {
    id: `demo-${normalizedName.replace(/\s+/g, '-')}-${hash.toString(16).slice(0, 8)}`,
    title: dishName,
    description: `Демонстрационная техкарта для блюда: ${dishName}`,
    category: 'demo',
    status: 'READY',
    portions: 1,
    ingredients,
    process_steps: processSteps,
    nutrition: {
      calories_per_100g: baseCalories,
      proteins_per_100g: baseProtein,
      fats_per_100g: baseFat,
      carbs_per_100g: baseCarbs,
      total_calories: Math.round(baseCalories * 2.5), // Assume ~250g portion
      total_proteins: Math.round(baseProtein * 2.5),
      total_fats: Math.round(baseFat * 2.5),
      total_carbs: Math.round(baseCarbs * 2.5)
    },
    cost: {
      total_cost: baseCost,
      cost_per_portion: baseCost,
      currency: 'RUB'
    },
    yield: {
      total: 250 + (hash % 200), // 250-450g
      per_portion: 250 + (hash % 200),
      unit: 'г'
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    meta: {
      isDemoData: true,
      demoReason: 'LLM недоступен из-за бюджетных ограничений - показаны умные демо-данные на основе названия блюда',
      generationMethod: 'smart_demo'
    }
  }
}

// Legacy function for compatibility
export const getDemoTechCard = (dishName: string): TechCardV2 | null => {
  return generateSmartDemoTechCard(dishName)
}