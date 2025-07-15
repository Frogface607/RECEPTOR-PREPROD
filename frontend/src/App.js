import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [showRegistration, setShowRegistration] = useState(false);
  const [cities, setCities] = useState([]);
  const [dishName, setDishName] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [techCard, setTechCard] = useState(null);
  const [userTechCards, setUserTechCards] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editInstruction, setEditInstruction] = useState('');
  const [isEditingAI, setIsEditingAI] = useState(false);
  const [currentTechCardId, setCurrentTechCardId] = useState(null);
  const [ingredients, setIngredients] = useState([]);

  // Subscription states
  const [subscriptionPlans, setSubscriptionPlans] = useState({});
  const [userSubscription, setUserSubscription] = useState(null);
  const [kitchenEquipment, setKitchenEquipment] = useState({});
  const [userEquipment, setUserEquipment] = useState([]);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [userHistory, setUserHistory] = useState([]);
  const [showTwistModal, setShowTwistModal] = useState(false);
  const [showPriceModal, setShowPriceModal] = useState(false);
  const [userPrices, setUserPrices] = useState([]);
  const [uploadingPrices, setUploadingPrices] = useState(false);
  const [editableIngredients, setEditableIngredients] = useState([]);
  const [isEditingIngredients, setIsEditingIngredients] = useState(false);
  const [editableSteps, setEditableSteps] = useState([]);
  const [isEditingSteps, setIsEditingSteps] = useState(false);

  // Instructions state
  const [showInstructions, setShowInstructions] = useState(false);

  // Interactive ingredients state
  const [currentIngredients, setCurrentIngredients] = useState([]);

  // PRO AI features state
  const [showProAIModal, setShowProAIModal] = useState(false);
  const [proAIResult, setProAIResult] = useState('');
  const [proAITitle, setProAITitle] = useState('');

  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('');
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [recognition, setRecognition] = useState(null);

  // Login states
  const [showLogin, setShowLogin] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  // Простая функция форматирования техкарты
  const formatTechCard = (content) => {
    if (!content) return null;

    // Извлекаем основные секции с помощью regex
    const extractSection = (pattern) => {
      const match = content.match(pattern);
      return match ? match[1].trim() : '';
    };

    const title = extractSection(/\*\*Название:\*\*\s*(.*?)(?=\n|$)/);
    const category = extractSection(/\*\*Категория:\*\*\s*(.*?)(?=\n|$)/);
    const description = extractSection(/\*\*Описание:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const ingredients = extractSection(/\*\*Ингредиенты:\*\*.*?\n\n(.*?)(?=\n\n|\*\*)/s);
    const recipe = extractSection(/\*\*Пошаговый рецепт:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const time = extractSection(/\*\*Время:\*\*\s*(.*?)(?=\n|$)/);
    const yieldAmount = extractSection(/\*\*Выход:\*\*\s*(.*?)(?=\n|$)/);
    const portion = extractSection(/\*\*Порция:\*\*\s*(.*?)(?=\n|$)/);
    const cost = extractSection(/\*\*Себестоимость:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const kbzhu1 = extractSection(/\*\*КБЖУ на 1 порцию:\*\*\s*(.*?)(?=\n|$)/);
    const kbzhu100 = extractSection(/\*\*КБЖУ на 100 г:\*\*\s*(.*?)(?=\n|$)/);
    const allergens = extractSection(/\*\*Аллергены:\*\*\s*(.*?)(?=\n|$)/);
    const storage = extractSection(/\*\*Заготовки и хранение:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const tips = extractSection(/\*\*Особенности и советы от шефа:\*\*\s*(.*?)(?=\n\n|\*\*)/s);
    const serving = extractSection(/\*\*Рекомендация подачи:\*\*\s*(.*?)(?=\n|$)/);

    return (
      <div className="space-y-6">
        {/* НАЗВАНИЕ */}
        {title && (
          <div className="text-center">
            <h1 className="text-3xl font-bold text-purple-300 mb-2">{title}</h1>
            {category && <p className="text-gray-400 text-lg">{category}</p>}
          </div>
        )}

        {/* ОПИСАНИЕ */}
        {description && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-lg font-bold text-purple-400 mb-3 uppercase tracking-wide">ОПИСАНИЕ</h3>
            <p className="text-gray-300 leading-relaxed">{description}</p>
          </div>
        )}

        {/* ИНГРЕДИЕНТЫ */}
        {ingredients && (
          <div className="bg-gradient-to-r from-purple-600/10 to-pink-600/10 border border-purple-400/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-purple-300 mb-4">ИНГРЕДИЕНТЫ</h3>
            <div className="space-y-2">
              {ingredients.split('\n').filter(line => line.trim()).map((line, idx) => (
                <p key={idx} className="text-gray-300">{line}</p>
              ))}
            </div>
          </div>
        )}

        {/* ВРЕМЯ И ВЫХОД */}
        {(time || yieldAmount || portion) && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {time && (
              <div className="bg-blue-900/20 rounded-lg p-4 text-center">
                <h4 className="text-blue-300 font-bold mb-2">ВРЕМЯ</h4>
                <p className="text-gray-300">{time}</p>
              </div>
            )}
            {yieldAmount && (
              <div className="bg-green-900/20 rounded-lg p-4 text-center">
                <h4 className="text-green-300 font-bold mb-2">ВЫХОД</h4>
                <p className="text-gray-300">{yieldAmount}</p>
              </div>
            )}
            {portion && (
              <div className="bg-purple-900/20 rounded-lg p-4 text-center">
                <h4 className="text-purple-300 font-bold mb-2">ПОРЦИЯ</h4>
                <p className="text-gray-300">{portion}</p>
              </div>
            )}
          </div>
        )}

        {/* СЕБЕСТОИМОСТЬ */}
        {cost && (
          <div className="bg-green-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-green-300 mb-4">СЕБЕСТОИМОСТЬ</h3>
            <div className="space-y-1">
              {cost.split('\n').filter(line => line.trim()).map((line, idx) => (
                <p key={idx} className="text-gray-300">{line}</p>
              ))}
            </div>
          </div>
        )}

        {/* ПОШАГОВЫЙ РЕЦЕПТ */}
        {recipe && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-xl font-bold text-purple-300 mb-4">ПОШАГОВЫЙ РЕЦЕПТ</h3>
            <div className="space-y-3">
              {recipe.split('\n').filter(line => line.trim()).map((line, idx) => (
                <div key={idx} className="flex items-start space-x-3">
                  <span className="text-purple-400 font-bold min-w-[2rem]">
                    {line.match(/^\d+\./) ? line.match(/^\d+/)[0] : '•'}
                  </span>
                  <p className="text-gray-300 flex-1">{line.replace(/^\d+\.\s*/, '')}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* КБЖУ */}
        {(kbzhu1 || kbzhu100) && (
          <div className="bg-yellow-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-yellow-300 mb-4">КБЖУ</h3>
            <div className="space-y-2">
              {kbzhu1 && <p className="text-gray-300"><strong>На 1 порцию:</strong> {kbzhu1}</p>}
              {kbzhu100 && <p className="text-gray-300"><strong>На 100 г:</strong> {kbzhu100}</p>}
            </div>
          </div>
        )}

        {/* АЛЛЕРГЕНЫ */}
        {allergens && (
          <div className="bg-red-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-red-300 mb-2">АЛЛЕРГЕНЫ</h3>
            <p className="text-gray-300">{allergens}</p>
          </div>
        )}

        {/* ЗАГОТОВКИ И ХРАНЕНИЕ */}
        {storage && (
          <div className="bg-gray-800/30 rounded-lg p-4">
            <h3 className="text-xl font-bold text-purple-300 mb-4">ЗАГОТОВКИ И ХРАНЕНИЕ</h3>
            <div className="space-y-2">
              {storage.split('\n').filter(line => line.trim()).map((line, idx) => (
                <p key={idx} className="text-gray-300">{line}</p>
              ))}
            </div>
          </div>
        )}

        {/* СОВЕТЫ ОТ ШЕФА */}
        {tips && (
          <div className="bg-gradient-to-r from-orange-900/20 to-red-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-orange-300 mb-4">СОВЕТЫ ОТ ШЕФА</h3>
            <div className="space-y-2">
              {tips.split('\n').filter(line => line.trim()).map((line, idx) => (
                <p key={idx} className="text-gray-300">{line}</p>
              ))}
            </div>
          </div>
        )}

        {/* РЕКОМЕНДАЦИЯ ПОДАЧИ */}
        {serving && (
          <div className="bg-pink-900/20 rounded-lg p-4">
            <h3 className="text-xl font-bold text-pink-300 mb-2">ПОДАЧА</h3>
            <p className="text-gray-300">{serving}</p>
          </div>
        )}
      </div>
    );
  };

  // Basic functions
  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API}/cities`);
      setCities(response.data);
    } catch (error) {
      console.error('Error fetching cities:', error);
    }
  };

  const fetchSubscriptionPlans = async () => {
    try {
      const response = await axios.get(`${API}/subscription-plans`);
      setSubscriptionPlans(response.data);
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
    }
  };

  const fetchKitchenEquipment = async () => {
    try {
      const response = await axios.get(`${API}/kitchen-equipment`);
      setKitchenEquipment(response.data);
    } catch (error) {
      console.error('Error fetching kitchen equipment:', error);
    }
  };

  const fetchUserSubscription = async () => {
    if (!currentUser?.id) return;
    try {
      const response = await axios.get(`${API}/user-subscription/${currentUser.id}`);
      setUserSubscription(response.data);
      setUserEquipment(response.data.kitchen_equipment || []);
    } catch (error) {
      console.error('Error fetching user subscription:', error);
    }
  };

  const fetchUserPrices = async () => {
    if (!currentUser?.id) return;
    try {
      const response = await axios.get(`${API}/user-prices/${currentUser.id}`);
      setUserPrices(response.data.prices || []);
    } catch (error) {
      console.error('Error fetching user prices:', error);
    }
  };

  const updateKitchenEquipment = async (equipmentIds) => {
    if (!currentUser?.id) return;
    try {
      await axios.post(`${API}/update-kitchen-equipment/${currentUser.id}`, {
        equipment_ids: equipmentIds
      });
      setUserEquipment(equipmentIds);
      setShowEquipmentModal(false);
      alert('Кухонное оборудование обновлено успешно!');
    } catch (error) {
      console.error('Error updating kitchen equipment:', error);
      alert('Ошибка при обновлении оборудования: ' + (error.response?.data?.detail || error.message));
    }
  };

  // ФУНКЦИИ ДЛЯ ИНТЕРАКТИВНОЙ ТАБЛИЦЫ ИНГРЕДИЕНТОВ
  const updateIngredient = (id, field, value) => {
    setCurrentIngredients(prev => prev.map(ing => 
      ing.id === id ? { ...ing, [field]: value } : ing
    ));
  };

  const removeIngredient = (id) => {
    setCurrentIngredients(prev => prev.filter(ing => ing.id !== id));
  };

  const addNewIngredient = () => {
    const newId = Math.max(...currentIngredients.map(ing => ing.id), 0) + 1;
    setCurrentIngredients(prev => [...prev, {
      id: newId,
      name: 'Новый ингредиент',
      quantity: '100 г',
      price: '~10 ₽',
      numericPrice: 10
    }]);
  };

  const saveIngredientsToTechCard = () => {
    // Обновляем техкарту с новыми ингредиентами
    const newIngredientsText = currentIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} — ${ing.price}`
    ).join('\n');
    
    const updatedTechCard = techCard.replace(
      /(\*\*Ингредиенты:\*\*)(.*?)(?=\*\*[^*]+:\*\*|$)/s,
      `$1\n\n${newIngredientsText}\n\n`
    );
    
    setTechCard(updatedTechCard);
    alert('Ингредиенты обновлены!');
  };

  // ПРО AI ФУНКЦИИ
  const generateSalesScript = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-sales-script`, {
        tech_card: techCard,
        user_id: currentUser.id
      });
      
      // Показываем результат в модальном окне
      setProAIResult(response.data.script);
      setProAITitle("🎭 СКРИПТ ПРОДАЖ ДЛЯ ОФИЦИАНТА");
      setShowProAIModal(true);
      
    } catch (error) {
      console.error('Error generating sales script:', error);
      alert('Ошибка при генерации скрипта продаж');
    } finally {
      setIsGenerating(false);
    }
  };

  const generateFoodPairing = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-food-pairing`, {
        tech_card: techCard,
        user_id: currentUser.id
      });
      
      setProAIResult(response.data.pairing);
      setProAITitle("ФУДПЕЙРИНГ И СОЧЕТАНИЯ");
      setShowProAIModal(true);
      
    } catch (error) {
      console.error('Error generating food pairing:', error);
      alert('Ошибка при генерации фудпейринга');
    } finally {
      setIsGenerating(false);
    }
  };

  const generatePhotoTips = async () => {
    if (!techCard || !currentUser?.id) return;
    
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-photo-tips`, {
        tech_card: techCard,
        user_id: currentUser.id
      });
      
      setProAIResult(response.data.tips);
      setProAITitle("СОВЕТЫ ПО ФОТОГРАФИИ БЛЮДА");
      setShowProAIModal(true);
      
    } catch (error) {
      console.error('Error generating photo tips:', error);
      alert('Ошибка при генерации советов по фото');
    } finally {
      setIsGenerating(false);
    }
  };

  // РЕВОЛЮЦИОННОЕ РЕШЕНИЕ: ИНТЕРАКТИВНАЯ ТАБЛИЦА ИНГРЕДИЕНТОВ
  const renderIngredientsTable = (content) => {
    console.log('=== INGREDIENTS TABLE DEBUG ===');
    console.log('Content received:', !!content);
    
    if (!content) {
      console.log('No content provided');
      return null;
    }
    
    // Извлекаем ингредиенты из техкарты 
    const ingredientsMatch = content.match(/\*\*Ингредиенты:\*\*(.*?)(?=\*\*[^*]+:\*\*|$)/s);
    console.log('Ingredients match found:', !!ingredientsMatch);
    
    if (ingredientsMatch) {
      const ingredientsText = ingredientsMatch[1];
      console.log('Ingredients text:', ingredientsText);
      
      const ingredientLines = ingredientsText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('-') && line.length > 5);
      
      console.log('Parsed ingredient lines:', ingredientLines);
      
      if (ingredientLines.length > 0) {
        // Парсим ингредиенты в структурированный формат
        const parsedIngredients = ingredientLines.map((line, index) => {
          const cleanLine = line.replace(/^-\s*/, '').trim();
          let name = '', quantity = '', price = '';
          
          // Парсим по формату: "Продукт — количество — ~цена"
          if (cleanLine.includes(' — ')) {
            const parts = cleanLine.split(' — ');
            name = parts[0] || '';
            quantity = parts[1] || '';
            price = parts[2] || '';
          } else if (cleanLine.includes(' - ')) {
            const parts = cleanLine.split(' - ');
            name = parts[0] || '';
            quantity = parts[1] || '';
            price = parts[2] || '';
          } else {
            name = cleanLine;
          }
          
          // Извлекаем числовую цену для расчетов
          const priceMatch = price.match(/(\d+(?:[.,]\d+)?)/);
          const numericPrice = priceMatch ? parseFloat(priceMatch[1].replace(',', '.')) : 0;
          
          return {
            id: index,
            name: name.trim(),
            quantity: quantity.trim(),
            price: price.trim(),
            numericPrice: numericPrice
          };
        });
        
        console.log('Parsed ingredients:', parsedIngredients);
        
        // Используем parsedIngredients напрямую вместо состояния
        const displayIngredients = parsedIngredients;
        
        // Рассчитываем общую стоимость
        const totalCost = displayIngredients.reduce((sum, ing) => sum + (ing.numericPrice || 0), 0);
        
        console.log('Total cost calculated:', totalCost);
        
        return (
          <div key="ingredients-table" className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-purple-300">ИНГРЕДИЕНТЫ</h3>
              <div className="text-sm text-purple-400">
                Всего позиций: {displayIngredients.length}
              </div>
            </div>
            
            {/* ИНТЕРАКТИВНАЯ ТАБЛИЦА */}
            <div className="overflow-x-auto bg-gray-800/50 rounded-lg">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-600 to-purple-700">
                    <th className="text-left py-3 px-4 text-white font-bold text-sm">ИНГРЕДИЕНТ</th>
                    <th className="text-center py-3 px-4 text-white font-bold text-sm">КОЛИЧЕСТВО</th>
                    <th className="text-right py-3 px-4 text-white font-bold text-sm">ЦЕНА</th>
                    <th className="text-center py-3 px-4 text-white font-bold text-sm">ДЕЙСТВИЯ</th>
                  </tr>
                </thead>
                <tbody>
                  {displayIngredients.map((ingredient, index) => (
                    <tr key={ingredient.id} className={index % 2 === 0 ? 'bg-gray-700/30' : 'bg-gray-600/30'}>
                      <td className="py-3 px-4 text-gray-200 border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.name}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            newIngredients[index] = { ...newIngredients[index], name: e.target.value };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-center border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.quantity}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            newIngredients[index] = { ...newIngredients[index], quantity: e.target.value };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 text-center hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-right border-r border-gray-600">
                        <input
                          type="text"
                          value={ingredient.price}
                          onChange={(e) => {
                            const newIngredients = [...displayIngredients];
                            const priceMatch = e.target.value.match(/(\d+(?:[.,]\d+)?)/);
                            const numericPrice = priceMatch ? parseFloat(priceMatch[1].replace(',', '.')) : 0;
                            newIngredients[index] = { 
                              ...newIngredients[index], 
                              price: e.target.value,
                              numericPrice: numericPrice
                            };
                            setCurrentIngredients(newIngredients);
                          }}
                          className="w-full bg-transparent border-none outline-none text-gray-200 text-right hover:bg-gray-700/50 rounded px-2 py-1"
                        />
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => {
                            const newIngredients = displayIngredients.filter((_, i) => i !== index);
                            setCurrentIngredients(newIngredients);
                          }}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* БЛОК С ОБЩЕЙ СТОИМОСТЬЮ */}
            <div className="mt-4 bg-gray-800/70 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold text-purple-300">Приблизительная себестоимость:</span>
                <span className="text-xl font-bold text-green-400">{Math.round(totalCost)} ₽</span>
              </div>
              <div className="mt-1 text-sm text-gray-400">
                *Рассчитывается из среднерыночных цен
              </div>
            </div>
            
            {/* КНОПКИ УПРАВЛЕНИЯ */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  const newId = Math.max(...displayIngredients.map(ing => ing.id), 0) + 1;
                  const newIngredients = [...displayIngredients, {
                    id: newId,
                    name: 'Новый ингредиент',
                    quantity: '100 г',
                    price: '~10 ₽',
                    numericPrice: 10
                  }];
                  setCurrentIngredients(newIngredients);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + ДОБАВИТЬ ИНГРЕДИЕНТ
              </button>
              <button
                onClick={() => {
                  // Обновляем техкарту с новыми ингредиентами
                  const newIngredientsText = displayIngredients.map(ing => 
                    `- ${ing.name} — ${ing.quantity} — ${ing.price}`
                  ).join('\n');
                  
                  const updatedTechCard = techCard.replace(
                    /(\*\*Ингредиенты:\*\*)(.*?)(?=\*\*[^*]+:\*\*|$)/s,
                    `$1\n\n${newIngredientsText}\n\n`
                  );
                  
                  setTechCard(updatedTechCard);
                  alert('Ингредиенты обновлены!');
                }}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                СОХРАНИТЬ ИЗМЕНЕНИЯ
              </button>
            </div>
          </div>
        );
      } else {
        console.log('No ingredient lines found');
      }
    } else {
      console.log('No ingredients section found');
    }
    
    // Если ингредиенты не найдены
    return (
      <div key="ingredients-error" className="bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-400/30 rounded-lg p-6 mb-6">
        <h3 className="text-xl font-bold text-red-300 mb-4">ИНГРЕДИЕНТЫ</h3>
        <p className="text-red-300">Ингредиенты не найдены в техкарте. Попробуйте сгенерировать заново.</p>
      </div>
    );
  };

  const handleEditTechCard = async () => {
    if (!editInstruction.trim() || !currentTechCardId) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: currentTechCardId,
        edit_instruction: editInstruction,
        user_id: currentUser.id
      });
      
      setTechCard(response.data.tech_card);
      setEditInstruction('');
      
      // Re-parse ingredients and steps for editing
      const lines = response.data.tech_card.split('\n');
      const ingredients = [];
      const steps = [];
      
      lines.forEach(line => {
        // Parse ingredients
        if (line.startsWith('- ') && line.includes('₽')) {
          const parts = line.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            ingredients.push({
              name: parts[0].trim(),
              quantity: parts[1].trim(),
              price: parts[2].trim()
            });
          }
        }
        
        // Parse numbered steps
        if (line.match(/^\d+\./)) {
          steps.push(line);
        }
      });
      
      setEditableIngredients(ingredients);
      setEditableSteps(steps);
      
    } catch (error) {
      console.error('Error editing tech card:', error);
      alert('Ошибка при редактировании техкарты');
    } finally {
      setIsEditingAI(false);
    }
  };

  const saveIngredientsChanges = () => {
    // Rebuild tech card with new ingredients
    const lines = techCard.split('\n');
    const newLines = [];
    let inIngredientsSection = false;
    let ingredientIndex = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('**Ингредиенты:**')) {
        inIngredientsSection = true;
        newLines.push(line);
        
        // Add updated ingredients
        editableIngredients.forEach(ing => {
          newLines.push(`- ${ing.name} — ${ing.quantity} — ${ing.price}`);
        });
        
        // Skip original ingredients
        continue;
      }
      
      if (inIngredientsSection && line.startsWith('- ') && line.includes('₽')) {
        // Skip original ingredient lines
        continue;
      }
      
      if (inIngredientsSection && line.startsWith('**') && line !== '**Ингредиенты:**') {
        inIngredientsSection = false;
      }
      
      newLines.push(line);
    }
    
    setTechCard(newLines.join('\n'));
    setIsEditingIngredients(false);
  };

  const saveStepsChanges = () => {
    // Rebuild tech card with new steps
    const lines = techCard.split('\n');
    const newLines = [];
    let inStepsSection = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      if (line.includes('**Пошаговый рецепт:**')) {
        inStepsSection = true;
        newLines.push(line);
        newLines.push('');
        
        // Add updated steps
        editableSteps.forEach((step, index) => {
          newLines.push(`${index + 1}. ${step}`);
        });
        
        continue;
      }
      
      if (inStepsSection && line.match(/^\d+\./)) {
        // Skip original step lines
        continue;
      }
      
      if (inStepsSection && line.startsWith('**') && !line.includes('Пошаговый рецепт')) {
        inStepsSection = false;
      }
      
      newLines.push(line);
    }
    
    setTechCard(newLines.join('\n'));
    setIsEditingSteps(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!loginEmail) {
      alert('Введите email');
      return;
    }
    
    try {
      console.log('Attempting login with email:', loginEmail);
      const response = await axios.get(`${API}/user/${loginEmail}`);
      console.log('Login successful:', response.data);
      
      // Update state immediately
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      
      // Reset form
      setShowLogin(false);
      setLoginEmail('');
      
      console.log('User logged in:', response.data);
      
    } catch (error) {
      console.error('Login error:', error);
      if (error.response?.status === 404) {
        alert('Пользователь не найден. Попробуйте зарегистрироваться.');
      } else {
        alert('Ошибка входа. Попробуйте еще раз.');
      }
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!registrationData.email || !registrationData.name || !registrationData.city) {
      alert('Пожалуйста, заполните все поля');
      return;
    }
    
    try {
      console.log('Attempting registration with data:', registrationData);
      const response = await axios.post(`${API}/register`, registrationData);
      console.log('Registration successful:', response.data);
      
      // Update state immediately
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      
      // Reset form
      setShowRegistration(false);
      setRegistrationData({ email: '', name: '', city: '' });
      
      // Force re-render by setting a flag
      console.log('User set to:', response.data);
      
    } catch (error) {
      console.error('Registration error:', error);
      if (error.response?.data?.detail) {
        alert(`Ошибка: ${error.response.data.detail}`);
      } else {
        alert('Ошибка регистрации. Попробуйте еще раз.');
      }
    }
  };

  const handleGenerateTechCard = async (e) => {
    e.preventDefault();
    console.log('Generate button clicked');
    console.log('Dish name:', dishName);
    console.log('Current user:', currentUser);
    
    if (!dishName.trim()) {
      console.log('No dish name provided');
      return;
    }

    setIsGenerating(true);
    try {
      console.log('Sending request to:', `${API}/generate-tech-card`);
      const response = await axios.post(`${API}/generate-tech-card`, {
        dish_name: dishName,
        user_id: currentUser.id
      });
      
      console.log('Tech card generation response:', response.data);
      setTechCard(response.data.tech_card);
      setCurrentTechCardId(response.data.id);
      
      // Add to history
      fetchUserHistory();
      // Parse ingredients and steps for editing
      const lines = response.data.tech_card.split('\n');
      const ingredients = [];
      const steps = [];
      
      lines.forEach(line => {
        // Parse ingredients
        if (line.startsWith('- ') && line.includes('₽')) {
          const parts = line.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            const name = parts[0].trim();
            const quantityStr = parts[1].trim(); // "250 г" или "300 мл"
            const priceStr = parts[2].trim(); // "~800 ₽"
            
            // Парсим количество и единицы измерения
            const quantityMatch = quantityStr.match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]+|г|кг|мл|л|шт)/);
            const quantity = quantityMatch ? quantityMatch[1] : '100';
            const unit = quantityMatch ? quantityMatch[2] : 'г';
            
            // Парсим цену
            const priceMatch = priceStr.match(/(\d+(?:\.\d+)?)/);
            const totalPrice = priceMatch ? priceMatch[1] : '0';
            
            // Рассчитываем цену за единицу
            const pricePerUnit = parseFloat(totalPrice) / parseFloat(quantity);
            
            ingredients.push({
              name: name,
              quantity: quantity,
              unit: unit,
              originalQuantity: quantity, // Сохраняем оригинальное количество
              originalPrice: totalPrice,  // Сохраняем оригинальную цену
              totalPrice: totalPrice,
              id: Date.now() + Math.random() + ingredients.length
            });
          }
        }
        
        // Parse numbered steps
        if (line.match(/^\d+\./)) {
          steps.push(line);
        }
      });
      
      // Загружаем парсированные ингредиенты в редактор
      setCurrentIngredients(ingredients);
      setEditableIngredients(ingredients);
      setEditableSteps(steps);
      
    } catch (error) {
      console.error('Error generating tech card:', error);
      alert('Ошибка при генерации техкарты');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePriceFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingPrices(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', currentUser.id);

    try {
      const response = await axios.post(`${API}/upload-prices`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('Upload response:', response.data);
      
      if (response.data.success) {
        alert(`Прайс-лист успешно загружен! Обработано ${response.data.count} позиций в ${response.data.categories_found} категориях`);
        setUserPrices(response.data.prices || []);
        setShowPriceModal(false);
      } else {
        alert('Ошибка при загрузке прайс-листа');
      }
    } catch (error) {
      console.error('Error uploading prices:', error);
      alert('Ошибка при загрузке файла: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploadingPrices(false);
    }
  };

  const fetchUserHistory = async () => {
    if (!currentUser?.id) {
      console.log('No user ID available for history fetch');
      return;
    }
    
    try {
      console.log('Fetching history for user:', currentUser.id);
      const response = await axios.get(`${API}/user-history/${currentUser.id}`);
      console.log('History response:', response.data);
      setUserHistory(response.data.history || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('receptor_user');
    setTechCard(null);
    setUserTechCards([]);
  };

  const handlePrintTechCard = () => {
    const dishName = techCard.split('\n').find(line => line.includes('Название'))?.replace(/\*\*/g, '').replace('Название:', '').trim() || 'Техкарта';
    const printWindow = window.open('', '_blank');
    
    // Process content to clean up formatting
    const cleanedContent = techCard.split('\n').map(line => {
      // Remove all ** formatting
      let cleanLine = line.replace(/\*\*/g, '');
      
      // Format headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = cleanLine.replace(':', '').trim();
        if (title.includes('Название')) {
          const dishTitle = title.replace('Название', '').trim();
          return `<h1 style="color: #8B5CF6; font-size: 28px; font-weight: 900; text-align: center; margin-bottom: 30px; border-bottom: 3px solid #8B5CF6; padding-bottom: 15px;">${dishTitle}</h1>`;
        }
        return `<h2 style="color: #1A1B23; font-size: 18px; font-weight: 800; text-transform: uppercase; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #C084FC; padding-bottom: 8px;">${title}</h2>`;
      }
      
      // Format ingredients
      if (line.startsWith('- ') && (line.includes('₽') || line.includes('руб'))) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Format numbered steps
      if (line.match(/^\d+\./)) {
        return `<div style="background: #F8FAFC; border-left: 4px solid #8B5CF6; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">${cleanLine}</div>`;
      }
      
      // Format list items
      if (line.startsWith('- ')) {
        return `<p style="margin-left: 20px; margin-bottom: 8px;">• ${cleanLine.replace('- ', '')}</p>`;
      }
      
      // Cost information
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена')) {
        return `<div style="background: #F0FDF4; border: 2px solid #10B981; border-radius: 8px; padding: 15px; margin: 15px 0; font-weight: 700;">${cleanLine}</div>`;
      }
      
      // Regular paragraphs
      if (cleanLine.trim() && !cleanLine.startsWith('─')) {
        return `<p style="margin-bottom: 12px; line-height: 1.6;">${cleanLine}</p>`;
      }
      
      return '';
    }).filter(Boolean).join('');
    
    const techCardHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Технологическая карта - ${dishName}</title>
          <meta charset="utf-8">
          <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
          <style>
            * { font-family: 'Montserrat', sans-serif !important; }
            body { 
              line-height: 1.6; 
              margin: 40px; 
              background: white; 
              color: #1A1B23; 
            }
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #8B5CF6; font-size: 32px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          </div>
          <div>${cleanedContent}</div>
          <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #64748B; border-top: 1px solid #E5E7EB; padding-top: 20px;">
            <p><strong>Сгенерировано RECEPTOR AI</strong></p>
            <p>Дата создания: ${new Date().toLocaleDateString('ru-RU')}</p>
          </div>
        </body>
      </html>
    `;
    
    printWindow.document.write(techCardHtml);
    printWindow.document.close();
    
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  const startVoiceRecognition = () => {
    if (recognition) {
      recognition.start();
    } else {
      console.log('Speech recognition not initialized');
    }
  };

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'ru-RU';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
        setVoiceStatus('Слушаю...');
        setShowVoiceModal(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setDishName(transcript);
        setVoiceStatus('Распознано: ' + transcript);
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 1500);
      };
      
      recognitionInstance.onerror = (event) => {
        setVoiceStatus('Ошибка распознавания');
        setIsListening(false);
        setTimeout(() => {
          setShowVoiceModal(false);
        }, 2000);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
        if (showVoiceModal) {
          setTimeout(() => {
            setShowVoiceModal(false);
          }, 1000);
        }
      };
      
      setRecognition(recognitionInstance);
    } else {
      console.log('Speech recognition not supported');
    }
  };

  useEffect(() => {
    fetchCities();
    fetchSubscriptionPlans();
    fetchKitchenEquipment();
    initVoiceRecognition();
    const savedUser = localStorage.getItem('receptor_user');
    console.log('Checking for saved user:', savedUser);
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      console.log('Setting currentUser from localStorage:', parsedUser);
      setCurrentUser(parsedUser);
      
      // Load user prices for PRO users
      if (parsedUser.subscription_plan === 'pro' || parsedUser.subscription_plan === 'business') {
        loadUserPrices(parsedUser.id);
      }
    }
  }, []);

  // Fetch subscription data when user changes
  useEffect(() => {
    if (currentUser?.id) {
      fetchUserSubscription();
      fetchUserHistory();
      fetchUserPrices();
    }
  }, [currentUser?.id]);

  const loadUserPrices = async (userId) => {
    try {
      const response = await axios.get(`${API}/user-prices/${userId}`);
      setUserPrices(response.data.prices || []);
    } catch (error) {
      console.error('Error loading user prices:', error);
    }
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center p-4">
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-gray-700">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-purple-300 mb-2">RECEPTOR PRO</h1>
            <p className="text-gray-400">AI для создания техкарт</p>
          </div>

          {!showRegistration && !showLogin ? (
            <div className="space-y-6">
              <button
                onClick={() => setShowRegistration(true)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                НАЧАТЬ РАБОТУ
              </button>
              <button
                onClick={() => setShowLogin(true)}
                className="w-full bg-gradient-to-r from-gray-600 to-gray-700 text-white font-bold py-3 px-6 rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all"
              >
                ВОЙТИ
              </button>
            </div>
          ) : showLogin ? (
            <form onSubmit={handleLogin} className="space-y-6">
              <input
                type="email"
                placeholder="Email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all"
              >
                ВОЙТИ
              </button>
              <button
                type="button"
                onClick={() => setShowLogin(false)}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
              >
                НАЗАД
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-6">
              <input
                type="email"
                placeholder="Email"
                value={registrationData.email}
                onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <input
                type="text"
                placeholder="Имя"
                value={registrationData.name}
                onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              />
              <select
                value={registrationData.city}
                onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none"
                required
              >
                <option value="">Выберите город</option>
                {cities.map(city => (
                  <option key={city.code} value={city.code}>{city.name}</option>
                ))}
              </select>
              <button
                type="submit"
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                ЗАРЕГИСТРИРОВАТЬСЯ
              </button>
              <button
                type="button"
                onClick={() => setShowRegistration(false)}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-all"
              >
                НАЗАД
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white font-['Montserrat']">
      {/* Header */}
      <header className="border-b border-purple-400/30 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold text-purple-300">RECEPTOR PRO</h1>
          
          {/* Subscription Info */}
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className="text-sm text-purple-300 font-bold">
                {currentUser.subscription_plan?.toUpperCase() || 'FREE'}
              </div>
              {currentUser.subscription_plan === 'free' && (
                <div className="text-xs text-gray-400">
                  {currentUser.monthly_tech_cards_used || 0}/3 техкарт
                </div>
              )}
              {currentUser.subscription_plan === 'starter' && (
                <div className="text-xs text-gray-400">
                  {currentUser.monthly_tech_cards_used || 0}/25 техкарт
                </div>
              )}
              {(currentUser.subscription_plan === 'pro' || currentUser.subscription_plan === 'business') && (
                <div className="text-xs text-gray-400">
                  {currentUser.monthly_tech_cards_used || 0} техкарт
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-6">
              <button
                onClick={() => {
                  setShowHistory(!showHistory);
                  if (!showHistory) {
                    fetchUserHistory();
                  }
                }}
                className="text-purple-300 hover:text-purple-200 font-semibold"
              >
                ИСТОРИЯ
              </button>
              <span className="text-purple-300 font-bold">{currentUser.name}</span>
              <button
                onClick={handleLogout}
                className="text-purple-300 hover:text-purple-200 font-semibold"
              >
                ВЫЙТИ
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left Panel */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700 space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-purple-300 mb-6">СОЗДАТЬ ТЕХКАРТУ</h2>
                    
                {/* Instructions Section */}
                <div className="border-t border-purple-400/30 pt-6 mb-6">
                  <div className="flex items-center space-x-2 mb-4 cursor-pointer" onClick={() => setShowInstructions(!showInstructions)}>
                    <span className="text-lg font-bold text-purple-300">ДЛЯ ЛУЧШЕГО РЕЗУЛЬТАТА</span>
                    <span className="text-purple-300 text-xl">❓</span>
                  </div>
                  {showInstructions && (
                    <div className="bg-gray-800/50 rounded-lg p-4 text-sm text-gray-300 space-y-2">
                      <p>• <strong>Укажите все подробно:</strong> тип блюда, способ приготовления, желаемый выход готового блюда</p>
                      <p>• <strong>Себестоимость:</strong> рассчитывается исходя из рыночных цен на 2024 год</p>
                      <p>• <strong>Проверяйте данные:</strong> нейросеть может ошибаться, стоит проверить расчеты</p>
                      <p>• <strong>Ручная корректировка:</strong> вы можете все вручную поправить через кнопку "Редактировать"</p>
                      <p>• <strong>Свой прайс-лист:</strong> загрузите свой прайс-лист для идеального расчета исходя из актуальных цен</p>
                      <p>• <strong>Пример:</strong> "Стейк из говядины на 4 порции, средней прожарки, общий выход 800г"</p>
                    </div>
                  )}
                </div>

                    <form onSubmit={handleGenerateTechCard} className="space-y-6">
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      НАЗВАНИЕ БЛЮДА
                    </label>
                    <div className="relative">
                      <textarea
                        value={dishName}
                        onChange={(e) => setDishName(e.target.value)}
                        placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                        className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none"
                        rows={5}
                        required
                      />
                      <button
                        type="button"
                        onClick={startVoiceRecognition}
                        disabled={isListening}
                        className={`absolute right-2 bottom-2 p-2 rounded-lg transition-colors ${
                          isListening 
                            ? 'bg-red-600 animate-pulse' 
                            : 'bg-purple-600 hover:bg-purple-700'
                        } text-white`}
                        title="Голосовой ввод"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={!dishName.trim() || isGenerating}
                    className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                  >
                    {isGenerating ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        СОЗДАЮ ТЕХКАРТУ...
                      </>
                    ) : 'СОЗДАТЬ ТЕХКАРТУ'}
                  </button>
                </form>
                
                {/* PRO Price Management */}
                {(currentUser.subscription_plan === 'pro' || currentUser.subscription_plan === 'business') && (
                  <div className="border-t border-purple-400/30 pt-6">
                    <h3 className="text-lg font-bold text-purple-300 mb-4">PRO ФУНКЦИИ</h3>
                    
                    {/* Kitchen Equipment Button */}
                    <button
                      onClick={() => setShowEquipmentModal(true)}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 px-6 rounded-lg transition-colors mb-4"
                    >
                      🔧 КУХОННОЕ ОБОРУДОВАНИЕ
                    </button>
                    {userEquipment.length > 0 && (
                      <div className="text-sm text-purple-400 text-center mb-4">
                        Выбрано {userEquipment.length} единиц оборудования
                      </div>
                    )}
                    
                    {/* Price Management Button */}
                    <button
                      onClick={() => setShowPriceModal(true)}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 px-6 rounded-lg transition-colors mb-4"
                    >
                      УПРАВЛЕНИЕ ПРАЙСАМИ
                    </button>
                    {userPrices.length > 0 && (
                      <div className="text-sm text-green-400 text-center mb-4">
                        Загружено {userPrices.length} позиций
                      </div>
                    )}
                    
                    {/* ПРО AI функции */}
                    <div className="border-t border-purple-400/20 pt-4">
                      <h4 className="text-md font-bold text-purple-200 mb-3">AI ДОПОЛНЕНИЯ</h4>
                      
                      <button
                        onClick={() => generateSalesScript()}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-2 px-4 rounded-lg transition-colors mb-3 text-sm"
                      >
                        🎭 СКРИПТ ПРОДАЖ
                      </button>
                      
                      <button
                        onClick={() => generateFoodPairing()}
                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-2 px-4 rounded-lg transition-colors mb-3 text-sm"
                      >
                        ФУДПЕЙРИНГ
                      </button>
                      
                      <button
                        onClick={() => generatePhotoTips()}
                        className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors mb-3 text-sm"
                      >
                        СОВЕТЫ ПО ФОТО
                      </button>
                    </div>
                  </div>
                )}
                
                {/* Upgrade prompt for Free users */}
                {currentUser.subscription_plan === 'free' && currentUser.monthly_tech_cards_used >= 3 && (
                  <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-4 mt-4">
                    <h3 className="text-lg font-bold text-purple-300 mb-2">ЛИМИТ ИСЧЕРПАН</h3>
                    <p className="text-gray-300 text-sm mb-3">
                      Вы использовали все 3 техкарты в месяце. Обновите подписку для неограниченного доступа!
                    </p>
                    <button
                      onClick={() => alert('Функция обновления подписки скоро будет доступна')}
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-2 px-4 rounded-lg transition-all hover:from-purple-700 hover:to-pink-700"
                    >
                      ОБНОВИТЬ ПОДПИСКУ
                    </button>
                  </div>
                )}
              </div>

              {/* AI Editing */}
              {techCard && (
                <div className="border-t border-purple-400/30 pt-8">
                  <h3 className="text-xl font-bold text-purple-300 mb-6">
                    РЕДАКТИРОВАТЬ ЧЕРЕЗ AI
                  </h3>
                  <div className="space-y-4">
                    <textarea
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="Детально опишите что изменить. Например: увеличить порцию в 2 раза, заменить картофель на рис"
                      className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[100px] resize-none"
                      rows={4}
                    />
                    <button
                      onClick={handleEditTechCard}
                      disabled={!editInstruction.trim() || isEditingAI}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center justify-center"
                    >
                      {isEditingAI ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          ОБРАБАТЫВАЮ...
                        </>
                      ) : 'ИЗМЕНИТЬ ЧЕРЕЗ AI'}
                    </button>
                  </div>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && techCard && (
                <div className="border-t border-purple-400/30 pt-8">
                  <h3 className="text-xl font-bold text-purple-300 mb-6">
                    РУЧНОЕ РЕДАКТИРОВАНИЕ
                  </h3>
                  <div className="space-y-4">
                    <button
                      onClick={() => setIsEditingIngredients(true)}
                      className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      РЕДАКТИРОВАТЬ ИНГРЕДИЕНТЫ
                    </button>
                    <button
                      onClick={() => setIsEditingSteps(true)}
                      className="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                    >
                      РЕДАКТИРОВАТЬ ЭТАПЫ
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2">
            {techCard ? (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
                  <h2 className="text-2xl font-bold text-purple-300">ТЕХНОЛОГИЧЕСКАЯ КАРТА</h2>
                  <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
                    <button 
                      onClick={() => navigator.clipboard.writeText(techCard)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      КОПИРОВАТЬ
                    </button>
                    <button 
                      onClick={handlePrintTechCard}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      ЭКСПОРТ В PDF
                    </button>
                    <button 
                      onClick={() => setShowTwistModal(true)}
                      className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      ТВИСТ
                    </button>
                  </div>
                </div>
                <div className="prose prose-invert max-w-none">
                  {formatTechCard(techCard)}
                </div>
                
                {/* ВСТРОЕННЫЙ РЕДАКТОР ИНГРЕДИЕНТОВ */}
                <div className="mt-8 bg-gradient-to-r from-purple-600/20 to-pink-600/20 border border-purple-400/30 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-purple-300">РЕДАКТОР ИНГРЕДИЕНТОВ</h3>
                    <div className="flex space-x-3">
                      <button 
                        onClick={() => {
                          setCurrentIngredients([...currentIngredients, { 
                            name: '', 
                            quantity: '', 
                            price: '',
                            id: Date.now() 
                          }]);
                        }}
                        className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold transition-colors flex items-center space-x-2"
                      >
                        <span>+</span>
                        <span>ДОБАВИТЬ</span>
                      </button>
                      <button 
                        onClick={() => {
                          // Логика сохранения изменений в техкарту
                          console.log('Сохраняем изменения ингредиентов:', currentIngredients);
                          
                          // Обновляем техкарту с новыми ингредиентами
                          const lines = techCard.split('\n');
                          const newLines = [];
                          let inIngredientsSection = false;
                          
                          for (let i = 0; i < lines.length; i++) {
                            const line = lines[i];
                            
                            if (line.includes('**Ингредиенты:**')) {
                              inIngredientsSection = true;
                              newLines.push(line);
                              newLines.push('');
                              
                              // Добавляем обновленные ингредиенты
                              currentIngredients.forEach(ing => {
                                newLines.push(`- ${ing.name} — ${ing.quantity} ${ing.unit} — ~${Math.round(parseFloat(ing.totalPrice) || 0)} ₽`);
                              });
                              continue;
                            }
                            
                            if (inIngredientsSection && line.startsWith('- ') && line.includes('₽')) {
                              // Пропускаем старые строки ингредиентов
                              continue;
                            }
                            
                            if (inIngredientsSection && line.startsWith('**') && !line.includes('Ингредиенты')) {
                              inIngredientsSection = false;
                            }
                            
                            newLines.push(line);
                          }
                          
                          setTechCard(newLines.join('\n'));
                          alert('Изменения ингредиентов сохранены!');
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-bold transition-colors flex items-center space-x-2"
                      >
                        <span>💾</span>
                        <span>СОХРАНИТЬ</span>
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {currentIngredients.length === 0 ? (
                      <div className="text-center py-8 text-gray-400">
                        <p className="mb-4">Ингредиенты из техкарты появятся здесь автоматически</p>
                      </div>
                    ) : (
                      <>
                        <div className="grid grid-cols-12 gap-3 text-sm font-bold text-purple-300 border-b border-purple-400/30 pb-2">
                          <span className="col-span-1">#</span>
                          <span className="col-span-6">ИНГРЕДИЕНТ</span>
                          <span className="col-span-3">КОЛИЧЕСТВО</span>
                          <span className="col-span-1">СТОИМОСТЬ</span>
                          <span className="col-span-1">✕</span>
                        </div>
                        {currentIngredients.map((ingredient, index) => (
                          <div key={ingredient.id || index} className="grid grid-cols-12 gap-3 bg-gray-800/50 rounded-lg p-3 hover:bg-gray-800/70 transition-colors">
                            <span className="col-span-1 text-purple-400 font-bold flex items-center justify-center">
                              {index + 1}.
                            </span>
                            <input
                              type="text"
                              value={ingredient.name}
                              onChange={(e) => {
                                const newIngredients = [...currentIngredients];
                                newIngredients[index].name = e.target.value;
                                setCurrentIngredients(newIngredients);
                              }}
                              placeholder="Название ингредиента"
                              className="col-span-6 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                            />
                            <input
                              type="text"
                              value={`${ingredient.quantity || ''} ${ingredient.unit || 'г'}`}
                              onChange={(e) => {
                                const newIngredients = [...currentIngredients];
                                const value = e.target.value;
                                // Парсим количество и единицу
                                const match = value.match(/(\d+(?:\.\d+)?)\s*([а-яёА-ЯЁ]+|г|кг|мл|л|шт|штук)?/);
                                if (match) {
                                  newIngredients[index].quantity = match[1];
                                  newIngredients[index].unit = match[2] || 'г';
                                  
                                  // Пересчитаем стоимость на основе изначальной цены за единицу
                                  const newQty = parseFloat(match[1]) || 0;
                                  const originalQty = parseFloat(ingredient.originalQuantity) || parseFloat(ingredient.quantity) || 1;
                                  const originalPrice = parseFloat(ingredient.originalPrice) || parseFloat(ingredient.totalPrice) || 0;
                                  
                                  // Пропорциональный пересчет
                                  newIngredients[index].totalPrice = ((originalPrice / originalQty) * newQty).toFixed(1);
                                }
                                setCurrentIngredients(newIngredients);
                              }}
                              placeholder="250 г"
                              className="col-span-3 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-gray-200 focus:border-purple-400 focus:outline-none"
                            />
                            <div className="col-span-1 flex items-center justify-center">
                              <span className="text-green-400 font-bold text-sm">
                                {Math.round(parseFloat(ingredient.totalPrice) || 0)} ₽
                              </span>
                            </div>
                            <button 
                              onClick={() => {
                                const newIngredients = currentIngredients.filter((_, i) => i !== index);
                                setCurrentIngredients(newIngredients);
                              }}
                              className="col-span-1 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors flex items-center justify-center text-lg"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                  
                  {currentIngredients.length > 0 && (
                    <div className="mt-6 p-4 bg-gray-800/30 rounded-lg border border-green-400/30">
                      <div className="grid grid-cols-3 gap-6 text-center">
                        <div>
                          <div className="text-gray-400 text-sm mb-1">ОБЩИЙ ВЫХОД ПОРЦИИ</div>
                          <div className="text-blue-400 font-bold text-xl">
                            {currentIngredients.reduce((total, ing) => {
                              return total + (parseFloat(ing.quantity) || 0);
                            }, 0).toFixed(0)} г
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-gray-400 text-sm mb-1">СЕБЕСТОИМОСТЬ ПОРЦИИ</div>
                          <div className="text-green-400 font-bold text-xl">
                            {Math.round(currentIngredients.reduce((total, ing) => {
                              return total + (parseFloat(ing.totalPrice) || 0);
                            }, 0))} ₽
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            *Примерная себестоимость
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-gray-400 text-sm mb-1">РЕКОМЕНДУЕМАЯ ЦЕНА</div>
                          <div className="text-purple-400 font-bold text-xl">
                            {Math.round(currentIngredients.reduce((total, ing) => {
                              return total + (parseFloat(ing.totalPrice) || 0);
                            }, 0) * 3)} ₽
                          </div>
                          <div className="text-gray-500 text-xs mt-1">
                            Маржа 200%
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-4 text-xs text-gray-500 text-center">
                        Стоимость рассчитывается на основе рыночных цен + региональный коэффициент + инфляция
                      </div>
                    </div>
                  )}
                </div>

              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-12 border border-gray-700 text-center">
                <h3 className="text-2xl font-bold text-purple-300 mb-4">ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ</h3>
                <p className="text-gray-400">Введите название блюда слева и нажмите "СОЗДАТЬ ТЕХКАРТУ"</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 text-center border border-purple-500/30">
            <div className="mb-6">
              {isListening ? (
                <div className="w-20 h-20 mx-auto bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                  <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 715 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                </div>
              ) : (
                <div className="w-20 h-20 mx-auto bg-green-500 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </div>
            <h3 className="text-xl font-bold text-purple-300 mb-4">
              {isListening ? 'СЛУШАЮ...' : 'ГОТОВО!'}
            </h3>
            <p className="text-gray-300">
              {voiceStatus}
            </p>
            {!isListening && (
              <button
                onClick={() => setShowVoiceModal(false)}
                className="mt-6 bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            )}
          </div>
        </div>
      )}

      {/* Ingredients Editor Modal */}
      {isEditingIngredients && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <h3 className="text-2xl font-bold text-purple-300 mb-6">РЕДАКТОР ИНГРЕДИЕНТОВ</h3>
            
            {editableIngredients.map((ingredient, index) => (
              <div key={index} className="grid grid-cols-4 gap-4 mb-4">
                <input
                  type="text"
                  value={ingredient.name}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].name = e.target.value;
                    setEditableIngredients(newIngredients);
                  }}
                  className="col-span-2 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Ингредиент"
                />
                <input
                  type="text"
                  value={ingredient.quantity}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].quantity = e.target.value;
                    setEditableIngredients(newIngredients);
                  }}
                  className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Количество"
                />
                <input
                  type="text"
                  value={ingredient.price}
                  onChange={(e) => {
                    const newIngredients = [...editableIngredients];
                    newIngredients[index].price = e.target.value;
                    setEditableIngredients(newIngredients);
                    
                    // Auto-recalculate total cost
                    const totalCost = newIngredients.reduce((sum, ing) => {
                      return sum + (parseFloat(ing.totalPrice) || 0);
                    }, 0);
                    console.log('New total cost:', totalCost);
                  }}
                  className="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder="Цена"
                />
              </div>
            ))}
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => {
                  setEditableIngredients([...editableIngredients, { name: '', quantity: '', price: '' }]);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
              >
                ДОБАВИТЬ
              </button>
              <button
                onClick={saveIngredientsChanges}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
              <button
                onClick={() => setIsEditingIngredients(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Steps Editor Modal */}
      {isEditingSteps && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <h3 className="text-2xl font-bold text-purple-300 mb-6">РЕДАКТОР ЭТАПОВ</h3>
            
            {editableSteps.map((step, index) => (
              <div key={index} className="mb-4">
                <textarea
                  value={step}
                  onChange={(e) => {
                    const newSteps = [...editableSteps];
                    newSteps[index] = e.target.value;
                    setEditableSteps(newSteps);
                  }}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded border border-gray-600 focus:border-purple-500 outline-none"
                  placeholder={`Этап ${index + 1}`}
                  rows={3}
                />
              </div>
            ))}
            
            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => {
                  setEditableSteps([...editableSteps, '']);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
              >
                ДОБАВИТЬ ЭТАП
              </button>
              <button
                onClick={saveStepsChanges}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
              <button
                onClick={() => setIsEditingSteps(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">ИСТОРИЯ ТЕХКАРТ</h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {userHistory.length === 0 ? (
              <p className="text-gray-400 text-center py-8">История пуста</p>
            ) : (
              <div className="space-y-4">
                {userHistory.map((item, index) => (
                  <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-lg font-bold text-purple-300">
                        {item.content.split('\n')[0].replace('**Название:**', '').trim()}
                      </h4>
                      <span className="text-sm text-gray-400">
                        {new Date(item.created_at).toLocaleDateString('ru-RU')}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm mb-3">
                      {item.content.split('\n').find(line => line.includes('**Описание:**'))?.replace('**Описание:**', '').trim() || 'Без описания'}
                    </p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          setTechCard(item.content);
                          setCurrentTechCardId(item.id);
                          setShowHistory(false);
                        }}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm"
                      >
                        ОТКРЫТЬ
                      </button>
                      <button
                        onClick={() => navigator.clipboard.writeText(item.content)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        КОПИРОВАТЬ
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Price Management Modal - PRO only */}
      {showPriceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-green-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-green-300">УПРАВЛЕНИЕ ПРАЙСАМИ</h3>
              <button
                onClick={() => setShowPriceModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            {/* File Upload */}
            <div className="mb-6">
              <h4 className="text-lg font-bold text-green-300 mb-3">ЗАГРУЗИТЬ ПРАЙС</h4>
              <div className="border-2 border-dashed border-green-500/30 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handlePriceFileUpload}
                  className="hidden"
                  id="price-file-upload"
                />
                <label
                  htmlFor="price-file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-3">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <span className="text-green-300 font-bold">
                    {uploadingPrices ? 'ЗАГРУЖАЮ...' : 'ЗАГРУЗИТЬ EXCEL/CSV'}
                  </span>
                  <span className="text-gray-400 text-sm mt-1">
                    Поддерживаются форматы: .xlsx, .xls, .csv
                  </span>
                </label>
              </div>
            </div>
            
            {/* Current Prices */}
            {userPrices.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-green-300 mb-3">ЗАГРУЖЕННЫЕ ПРАЙСЫ</h4>
                <div className="bg-gray-800/50 rounded-lg max-h-60 overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-green-600 text-white sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left">Продукт</th>
                        <th className="px-4 py-2 text-center">Категория</th>
                        <th className="px-4 py-2 text-right">Цена</th>
                        <th className="px-4 py-2 text-center">Единица</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userPrices.slice(0, 15).map((price, index) => (
                        <tr key={index} className="border-b border-gray-700">
                          <td className="px-4 py-2 text-gray-300">{price.name}</td>
                          <td className="px-4 py-2 text-center">
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                              price.category === 'мясо' ? 'bg-red-600 text-white' :
                              price.category === 'овощи' ? 'bg-green-600 text-white' :
                              price.category === 'молочные' ? 'bg-blue-600 text-white' :
                              price.category === 'рыба' ? 'bg-cyan-600 text-white' :
                              'bg-gray-600 text-white'
                            }`}>
                              {price.category || 'прочее'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-right text-green-400">{price.price}₽</td>
                          <td className="px-4 py-2 text-center text-gray-400">{price.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {userPrices.length > 15 && (
                    <div className="text-center py-2 text-gray-400 text-sm">
                      ... и еще {userPrices.length - 15} позиций
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Instructions */}
            <div className="bg-blue-600/20 rounded-lg p-4 mb-6">
              <h4 className="text-blue-300 font-bold mb-2">УМНАЯ ОБРАБОТКА:</h4>
              <ul className="text-blue-200 text-sm space-y-1">
                <li>• <strong>Автоочистка:</strong> удаляет спецсимволы, исправляет сокращения</li>
                <li>• <strong>Категоризация:</strong> автоматически сортирует по типам продуктов</li>
                <li>• <strong>Нормализация:</strong> приводит единицы к стандарту (кг, л, шт)</li>
                <li>• <strong>Формат файла:</strong> A-название, B-цена, C-единица</li>
                <li>• <strong>Точность:</strong> расчет себестоимости до копейки!</li>
              </ul>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setUserPrices([])}
                disabled={userPrices.length === 0}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
              >
                ОЧИСТИТЬ ВСЕ
              </button>
              <button
                onClick={() => setShowPriceModal(false)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                ГОТОВО
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Twist Modal */}
      {showTwistModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 border border-orange-500/30">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center">
                <span className="text-2xl">🔥</span>
              </div>
              <h3 className="text-xl font-bold text-orange-300 mb-4">ТВИСТ НА БЛЮДО</h3>
              <p className="text-gray-300 mb-6 text-sm">
                Выберите стиль для интересной вариации вашего блюда
              </p>
              
              <div className="grid grid-cols-2 gap-3 mb-6">
                {[
                  { emoji: '🍜', text: 'Азиатский стиль', action: 'адаптируй под азиатскую кухню' },
                  { emoji: '🥗', text: 'Здоровое питание', action: 'сделай более здоровым и диетическим' },
                  { emoji: '🌱', text: 'Веганская версия', action: 'адаптируй для веганов, замени животные продукты' },
                  { emoji: '💎', text: 'Премиум вариант', action: 'сделай премиум версию с дорогими ингредиентами' },
                  { emoji: '⚡', text: 'Быстрое приготовление', action: 'упрости рецепт для быстрого приготовления' },
                  { emoji: '🔬', text: 'Молекулярная кухня', action: 'адаптируй под молекулярную кухню' },
                  { emoji: '🍂', text: 'Сезонные ингредиенты', action: 'используй сезонные ингредиенты' },
                  { emoji: '🚫', text: 'Безглютеновый', action: 'сделай безглютеновую версию' }
                ].map((twist, index) => (
                  <button
                    key={index}
                    onClick={async () => {
                      if (!techCard) return;
                      setShowTwistModal(false);
                      setIsGenerating(true);
                      try {
                        const response = await axios.post(`${API}/generate-tech-card`, {
                          dish_name: `${techCard.split('\n')[0]?.replace(/\*\*/g, '').replace('Название:', '').trim()} - ${twist.text}`,
                          city: currentUser.city,
                          user_id: currentUser.id,
                          twist_instruction: `Создай новую техкарту на основе этого блюда, но с поворотом "${twist.action}". Оригинальная техкарта: ${techCard}`
                        });
                        setTechCard(response.data.content);
                        setCurrentTechCardId(response.data.id);
                        alert(`Новая техкарта создана с поворотом "${twist.text}"!`);
                      } catch (error) {
                        console.error('Error creating twist:', error);
                        alert('Ошибка при создании поворота техкарты');
                      } finally {
                        setIsGenerating(false);
                      }
                    }}
                    className="bg-gray-700 hover:bg-orange-600 text-white p-3 rounded-lg transition-colors text-sm flex flex-col items-center"
                  >
                    <span className="text-lg mb-1">{twist.emoji}</span>
                    <span className="text-xs">{twist.text}</span>
                  </button>
                ))}
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={async () => {
                    const twists = [
                      { text: 'Азиатский стиль', action: 'адаптируй под азиатскую кухню' },
                      { text: 'Здоровое питание', action: 'сделай более здоровым и диетическим' },
                      { text: 'Веганская версия', action: 'адаптируй для веганов, замени животные продукты' },
                      { text: 'Премиум вариант', action: 'сделай премиум версию с дорогими ингредиентами' },
                      { text: 'Быстрое приготовление', action: 'упрости рецепт для быстрого приготовления' },
                      { text: 'Молекулярная кухня', action: 'адаптируй под молекулярную кухню' },
                      { text: 'Сезонные ингредиенты', action: 'используй сезонные ингредиенты' },
                      { text: 'Безглютеновый', action: 'сделай безглютеновую версию' }
                    ];
                    const randomTwist = twists[Math.floor(Math.random() * twists.length)];
                    
                    if (!techCard) return;
                    setShowTwistModal(false);
                    setIsGenerating(true);
                    try {
                      const response = await axios.post(`${API}/generate-tech-card`, {
                        dish_name: `${techCard.split('\n')[0]?.replace(/\*\*/g, '').replace('Название:', '').trim()} - ${randomTwist.text}`,
                        city: currentUser.city,
                        user_id: currentUser.id,
                        twist_instruction: `Создай новую техкарту на основе этого блюда, но с поворотом "${randomTwist.action}". Оригинальная техкарта: ${techCard}`
                      });
                      setTechCard(response.data.content);
                      setCurrentTechCardId(response.data.id);
                      alert(`Новая техкарта создана с поворотом "${randomTwist.text}"!`);
                    } catch (error) {
                      console.error('Error creating twist:', error);
                      alert('Ошибка при создании поворота техкарты');
                    } finally {
                      setIsGenerating(false);
                    }
                  }}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
                >
                  СЛУЧАЙНЫЙ
                </button>
                <button
                  onClick={() => setShowTwistModal(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
                >
                  ОТМЕНА
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 border border-purple-500/30">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center animate-pulse">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-purple-300 mb-4">ГОЛОСОВОЙ ВВОД</h3>
              <p className="text-gray-300 mb-6">
                {voiceStatus}
              </p>
              <button
                onClick={() => setShowVoiceModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Kitchen Equipment Modal */}
      {showEquipmentModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">КУХОННОЕ ОБОРУДОВАНИЕ</h3>
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-300 text-sm mb-4">
                Выберите оборудование, которое есть на вашей кухне. AI будет адаптировать рецепты под доступное оборудование.
              </p>
            </div>
            
            {kitchenEquipment.cooking_methods && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Способы приготовления</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.cooking_methods.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {kitchenEquipment.prep_equipment && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Подготовительное оборудование</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.prep_equipment.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            {kitchenEquipment.storage && (
              <div className="mb-6">
                <h4 className="text-lg font-bold text-purple-300 mb-3">Хранение</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {kitchenEquipment.storage.map(equipment => (
                    <label key={equipment.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={userEquipment.includes(equipment.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setUserEquipment([...userEquipment, equipment.id]);
                          } else {
                            setUserEquipment(userEquipment.filter(id => id !== equipment.id));
                          }
                        }}
                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-gray-300 text-sm">{equipment.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setShowEquipmentModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ОТМЕНА
              </button>
              <button
                onClick={() => updateKitchenEquipment(userEquipment)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                СОХРАНИТЬ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PRO AI Results Modal */}
      {showProAIModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto border border-purple-500/30">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-purple-300">{proAITitle}</h3>
              <button
                onClick={() => setShowProAIModal(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-6">
              <div className="text-gray-200 whitespace-pre-line">{proAIResult}</div>
            </div>
            
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => navigator.clipboard.writeText(proAIResult)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg"
              >
                📋 КОПИРОВАТЬ
              </button>
              <button
                onClick={() => setShowProAIModal(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
              >
                ЗАКРЫТЬ
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;