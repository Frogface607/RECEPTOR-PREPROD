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

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  useEffect(() => {
    fetchCities();
    // Check if user is already logged in
    const savedUser = localStorage.getItem('receptor_user');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      fetchUserTechCards();
    }
  }, [currentUser]);

  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API}/cities`);
      setCities(response.data);
    } catch (error) {
      console.error('Error fetching cities:', error);
    }
  };

  const fetchUserTechCards = async () => {
    try {
      const response = await axios.get(`${API}/tech-cards/${currentUser.id}`);
      setUserTechCards(response.data);
    } catch (error) {
      console.error('Error fetching tech cards:', error);
    }
  };

  const handleRegistration = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, registrationData);
      const user = response.data;
      setCurrentUser(user);
      localStorage.setItem('receptor_user', JSON.stringify(user));
      setShowRegistration(false);
    } catch (error) {
      if (error.response?.status === 400) {
        // User already exists, try to fetch
        try {
          const userResponse = await axios.get(`${API}/user/${registrationData.email}`);
          const user = userResponse.data;
          setCurrentUser(user);
          localStorage.setItem('receptor_user', JSON.stringify(user));
          setShowRegistration(false);
        } catch (fetchError) {
          console.error('Error fetching existing user:', fetchError);
        }
      } else {
        console.error('Registration error:', error);
      }
    }
  };

  const handleGenerateTechCard = async (e) => {
    e.preventDefault();
    if (!dishName.trim()) return;

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate-tech-card`, {
        dish_name: dishName,
        user_id: currentUser.id
      });
      
      setTechCard(response.data.tech_card);
      setCurrentTechCardId(response.data.id);
      setDishName('');
      setIsEditing(false);
      parseIngredients(response.data.tech_card);
      fetchUserTechCards(); // Refresh the list
    } catch (error) {
      console.error('Error generating tech card:', error);
      alert('Ошибка при генерации техкарты. Попробуйте еще раз.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditWithAI = async (e) => {
    e.preventDefault();
    if (!editInstruction.trim() || !currentTechCardId) return;

    setIsEditingAI(true);
    try {
      const response = await axios.post(`${API}/edit-tech-card`, {
        tech_card_id: currentTechCardId,
        edit_instruction: editInstruction
      });
      
      setTechCard(response.data.tech_card);
      setEditInstruction('');
      parseIngredients(response.data.tech_card);
      fetchUserTechCards(); // Refresh the list
    } catch (error) {
      console.error('Error editing tech card:', error);
      alert('Ошибка при редактировании техкарты. Попробуйте еще раз.');
    } finally {
      setIsEditingAI(false);
    }
  };

  const parseIngredients = async (techCardContent) => {
    try {
      const response = await axios.post(`${API}/parse-ingredients`, techCardContent, {
        headers: { 'Content-Type': 'text/plain' }
      });
      setIngredients(response.data.ingredients);
    } catch (error) {
      console.error('Error parsing ingredients:', error);
    }
  };

  const handleIngredientChange = (index, field, value) => {
    const newIngredients = [...ingredients];
    newIngredients[index][field] = value;
    setIngredients(newIngredients);
    
    // Auto-recalculate tech card with new ingredients
    updateTechCardWithIngredients(newIngredients);
  };

  const updateTechCardWithIngredients = (newIngredients) => {
    // Calculate new cost
    const totalCost = newIngredients.reduce((sum, ing) => sum + (ing.price || 0), 0);
    const recommendedPrice = Math.round(totalCost * 3);
    
    // Update tech card content with new prices
    let updatedContent = techCard;
    
    // Update ingredients section
    const ingredientsSection = newIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} — ~${ing.price} ₽`
    ).join('\n');
    
    // Replace ingredients section
    updatedContent = updatedContent.replace(
      /(\*\*Ингредиенты:\*\*\n\n)([\s\S]*?)(\n\n\*\*Пошаговый рецепт:\*\*)/,
      `$1${ingredientsSection}$3`
    );
    
    // Update cost section
    updatedContent = updatedContent.replace(
      /- По ингредиентам: \d+ ₽/,
      `- По ингредиентам: ${Math.round(totalCost)} ₽`
    );
    updatedContent = updatedContent.replace(
      /- Рекомендуемая цена \(×3\): \d+ ₽/,
      `- Рекомендуемая цена (×3): ${recommendedPrice} ₽`
    );
    
    setTechCard(updatedContent);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('receptor_user');
    setTechCard(null);
    setUserTechCards([]);
    setIsEditing(false);
    setCurrentTechCardId(null);
    setIngredients([]);
  };

  const handleSelectTechCard = (card) => {
    setTechCard(card.content);
    setCurrentTechCardId(card.id);
    setIsEditing(false);
    parseIngredients(card.content);
  };

  const handlePrintTechCard = () => {
    const dishName = techCard.split('\n')[0].replace('**Название:**', '').trim();
    const printWindow = window.open('', '_blank');
    const techCardHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Технологическая карта - ${dishName}</title>
          <meta charset="utf-8">
          <style>
            body { 
              font-family: 'Times New Roman', serif; 
              line-height: 1.6; 
              margin: 40px; 
              background: white; 
              color: black; 
            }
            h1 { 
              color: #4a5568; 
              font-size: 24px; 
              margin-bottom: 20px; 
              text-align: center; 
            }
            h2 { 
              color: #2d3748; 
              font-size: 18px; 
              margin-top: 25px; 
              margin-bottom: 10px; 
              border-bottom: 2px solid #e2e8f0; 
              padding-bottom: 5px; 
            }
            h3 { 
              color: #4a5568; 
              font-size: 16px; 
              margin-top: 20px; 
              margin-bottom: 8px; 
            }
            p { 
              margin-bottom: 8px; 
              font-size: 14px; 
            }
            .ingredient-list { 
              margin-left: 20px; 
            }
            .step-list { 
              margin-left: 20px; 
            }
            .highlight { 
              background-color: #f7fafc; 
              padding: 10px; 
              border-left: 4px solid #9f7aea; 
              margin: 10px 0; 
            }
            .cost-info { 
              background-color: #f0fff4; 
              padding: 15px; 
              border: 1px solid #68d391; 
              margin: 15px 0; 
            }
            .footer { 
              margin-top: 30px; 
              text-align: center; 
              font-size: 12px; 
              color: #718096; 
            }
            @media print {
              body { margin: 20px; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <h1>📋 ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          <div id="tech-card-content">
            ${formatTechCardForPrint(techCard)}
          </div>
          <div class="footer">
            <p>Сгенерировано RECEPTOR AI — экономьте 2 часа на каждой техкарте</p>
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

  const formatTechCardForPrint = (content) => {
    return content.split('\n').map(line => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return `<h2>${line.replace(/\*\*/g, '')}</h2>`;
      }
      if (line.startsWith('💡') || line.startsWith('🔥') || line.startsWith('🌀')) {
        return `<div class="highlight">${line}</div>`;
      }
      if (line.includes('Себестоимость:') || line.includes('Рекомендуемая цена')) {
        return `<div class="cost-info">${line}</div>`;
      }
      if (line.startsWith('- ')) {
        return `<p class="ingredient-list">${line}</p>`;
      }
      if (line.match(/^\d+\./)) {
        return `<p class="step-list">${line}</p>`;
      }
      if (line.trim()) {
        return `<p>${line}</p>`;
      }
      return '<br>';
    }).join('');
  };

  const formatTechCard = (content) => {
    return content.split('\n').map((line, index) => {
      // Main sections headers
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '');
        if (title.includes('Название:')) {
          return (
            <div key={index} className="mb-6">
              <h1 className="text-3xl font-bold text-center text-purple-100 mb-2 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                {title.replace('Название:', '').trim()}
              </h1>
            </div>
          );
        }
        return (
          <h2 key={index} className="text-xl font-bold text-purple-300 mt-6 mb-3 pb-2 border-b border-purple-500/30">
            {title}
          </h2>
        );
      }
      
      // Ingredients section - convert to table if we're not in editing mode
      if (line.startsWith('- ') && !isEditing && content.includes('**Ингредиенты:**')) {
        const isInIngredientsSection = content.split('\n').slice(0, index).some(l => l.includes('**Ингредиенты:**')) &&
                                      !content.split('\n').slice(0, index).some(l => l.includes('**Пошаговый рецепт:**'));
        
        if (isInIngredientsSection) {
          const parts = line.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            return (
              <tr key={index} className="border-b border-purple-500/20">
                <td className="text-purple-200 py-2">{parts[0].trim()}</td>
                <td className="text-gray-300 py-2 text-center">{parts[1].trim()}</td>
                <td className="text-green-300 py-2 text-right font-medium">{parts[2].trim()}</td>
              </tr>
            );
          }
        }
      }
      
      // Check if we need to start ingredients table
      if (line.includes('**Ингредиенты:**') && !isEditing) {
        const ingredientLines = content.split('\n').slice(index + 1).filter(l => l.startsWith('- ') && l.includes(' — '));
        const tableRows = ingredientLines.map((ingLine, ingIndex) => {
          const parts = ingLine.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            return (
              <tr key={`ing-${ingIndex}`} className="border-b border-purple-500/20 hover:bg-purple-900/20">
                <td className="text-purple-200 py-2 px-4">{parts[0].trim()}</td>
                <td className="text-gray-300 py-2 px-4 text-center">{parts[1].trim()}</td>
                <td className="text-green-300 py-2 px-4 text-right font-medium">{parts[2].trim()}</td>
              </tr>
            );
          }
          return null;
        }).filter(Boolean);
        
        if (tableRows.length > 0) {
          return (
            <div key={index} className="mb-6">
              <h2 className="text-xl font-bold text-purple-300 mt-6 mb-3 pb-2 border-b border-purple-500/30">
                Ингредиенты
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full bg-gray-800/30 rounded-lg overflow-hidden">
                  <thead className="bg-purple-600/30">
                    <tr>
                      <th className="text-purple-100 py-3 px-4 text-left">Ингредиент</th>
                      <th className="text-purple-100 py-3 px-4 text-center">Количество</th>
                      <th className="text-purple-100 py-3 px-4 text-right">Цена</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows}
                  </tbody>
                </table>
              </div>
            </div>
          );
        }
      }
      
      // Skip ingredient lines if we already processed them in table
      if (line.startsWith('- ') && !isEditing && content.includes('**Ингредиенты:**')) {
        const isInIngredientsSection = content.split('\n').slice(0, index).some(l => l.includes('**Ингредиенты:**')) &&
                                      !content.split('\n').slice(0, index).some(l => l.includes('**Пошаговый рецепт:**'));
        if (isInIngredientsSection && line.includes(' — ')) {
          return null; // Skip, already processed in table
        }
      }
      
      // Cost information - highlight important
      if (line.includes('Себестоимость:') || line.includes('Рекомендуемая цена')) {
        return (
          <div key={index} className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 mb-2">
            <p className="text-green-200 font-medium">{line}</p>
          </div>
        );
      }
      
      // Tips and advice
      if (line.startsWith('💡') || line.startsWith('🔥') || line.startsWith('🌀')) {
        const bgColor = line.startsWith('💡') ? 'bg-blue-900/20 border-blue-500/30' :
                       line.startsWith('🔥') ? 'bg-red-900/20 border-red-500/30' :
                       'bg-orange-900/20 border-orange-500/30';
        return (
          <div key={index} className={`${bgColor} border rounded-lg p-3 mb-2`}>
            <p className="text-indigo-200 italic">{line}</p>
          </div>
        );
      }
      
      // Food pairing
      if (line.startsWith('🍷') || line.startsWith('🍺') || line.startsWith('🍹')) {
        return (
          <p key={index} className="text-pink-200 mb-1 ml-4">
            {line}
          </p>
        );
      }
      
      // Sales script
      if (line.startsWith('💬')) {
        return (
          <div key={index} className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4 mb-2">
            <p className="text-green-200">{line}</p>
          </div>
        );
      }
      
      // Photography tips
      if (line.startsWith('📸')) {
        return (
          <div key={index} className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 mb-2">
            <p className="text-blue-200">{line}</p>
          </div>
        );
      }
      
      // Menu tags
      if (line.startsWith('🏷️')) {
        return (
          <p key={index} className="text-yellow-200 mb-2">
            {line}
          </p>
        );
      }
      
      // Regular list items
      if (line.startsWith('- ')) {
        return (
          <p key={index} className="text-gray-200 mb-1 ml-4">
            {line}
          </p>
        );
      }
      
      // Numbered steps
      if (line.match(/^\d+\./)) {
        return (
          <div key={index} className="bg-gray-800/30 rounded-lg p-3 mb-3 ml-4">
            <p className="text-gray-200">{line}</p>
          </div>
        );
      }
      
      // Regular paragraphs
      if (line.trim()) {
        return (
          <p key={index} className="text-gray-300 mb-2">
            {line}
          </p>
        );
      }
      
      return <div key={index} className="mb-2"></div>;
    }).filter(Boolean);
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-800">
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="max-w-md w-full">
            <div className="text-center mb-8">
              <div className="mb-4">
                <img 
                  src="/logo.png" 
                  alt="Receptor Logo" 
                  className="w-24 h-24 mx-auto mb-4"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
              <h1 className="text-4xl font-bold text-white mb-2">
                receptor
              </h1>
              <p className="text-purple-200 text-lg">
                AI-помощник для шеф-поваров
              </p>
              <p className="text-gray-300 mt-2">
                Создавайте технологические карты за секунды
              </p>
            </div>

            {!showRegistration ? (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                <h2 className="text-2xl font-bold text-white mb-6 text-center">
                  Добро пожаловать!
                </h2>
                <button
                  onClick={() => setShowRegistration(true)}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  Начать работу
                </button>
              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                <h2 className="text-2xl font-bold text-white mb-6 text-center">
                  Регистрация
                </h2>
                <form onSubmit={handleRegistration}>
                  <div className="mb-4">
                    <label className="block text-purple-200 text-sm font-medium mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={registrationData.email}
                      onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-purple-200 text-sm font-medium mb-2">
                      Имя
                    </label>
                    <input
                      type="text"
                      value={registrationData.name}
                      onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-purple-200 text-sm font-medium mb-2">
                      Город
                    </label>
                    <select
                      value={registrationData.city}
                      onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                      className="w-full px-4 py-2 bg-gray-700/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      required
                    >
                      <option value="">Выберите город</option>
                      {cities.map(city => (
                        <option key={city.code} value={city.code}>
                          {city.name} {city.coefficient !== 1.0 && `(${city.coefficient}x)`}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    Зарегистрироваться
                  </button>
                </form>
                <button
                  onClick={() => setShowRegistration(false)}
                  className="w-full mt-3 text-purple-300 hover:text-purple-200 text-sm"
                >
                  Назад
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-800">
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-purple-500/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">receptor</h1>
              <span className="ml-2 text-purple-300">AI для шеф-поваров</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-purple-200">
                {currentUser.name} ({cities.find(c => c.code === currentUser.city)?.name})
              </span>
              <button
                onClick={handleLogout}
                className="text-purple-300 hover:text-purple-200 text-sm"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Generation Form */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
              <h2 className="text-xl font-bold text-white mb-4">
                Создать техкарту
              </h2>
              <form onSubmit={handleGenerateTechCard}>
                <div className="mb-4">
                  <label className="block text-purple-200 text-sm font-medium mb-2">
                    Название блюда
                  </label>
                  <input
                    type="text"
                    value={dishName}
                    onChange={(e) => setDishName(e.target.value)}
                    placeholder="Например: Стейк с картофелем"
                    className="w-full px-4 py-2 bg-gray-700/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  {isGenerating ? 'Генерируется...' : 'Создать техкарту'}
                </button>
              </form>

              {/* AI Editing */}
              {techCard && (
                <div className="mt-6 border-t border-purple-500/20 pt-6">
                  <h3 className="text-lg font-bold text-white mb-4">
                    🤖 Редактировать через AI
                  </h3>
                  <form onSubmit={handleEditWithAI}>
                    <div className="mb-4">
                      <input
                        type="text"
                        value={editInstruction}
                        onChange={(e) => setEditInstruction(e.target.value)}
                        placeholder="Например: увеличить порцию в 2 раза"
                        className="w-full px-4 py-2 bg-gray-700/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={isEditingAI || !editInstruction.trim()}
                      className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200"
                    >
                      {isEditingAI ? 'Редактируется...' : 'Изменить через AI'}
                    </button>
                  </form>
                  
                  <div className="mt-4">
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200"
                    >
                      {isEditing ? '📝 Закрыть редактор' : '✏️ Ручное редактирование'}
                    </button>
                  </div>
                </div>
              )}

              {/* Manual Ingredient Editing */}
              {isEditing && ingredients.length > 0 && (
                <div className="mt-6 border-t border-purple-500/20 pt-6">
                  <h3 className="text-lg font-bold text-white mb-4">
                    ✏️ Редактировать ингредиенты
                  </h3>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {ingredients.map((ingredient, index) => (
                      <div key={index} className="bg-gray-700/30 rounded-lg p-3">
                        <div className="text-purple-200 text-sm mb-2">{ingredient.name}</div>
                        <div className="grid grid-cols-2 gap-2">
                          <input
                            type="text"
                            value={ingredient.quantity}
                            onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                            className="px-2 py-1 bg-gray-600/50 border border-purple-500/30 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
                            placeholder="Количество"
                          />
                          <input
                            type="number"
                            value={ingredient.price}
                            onChange={(e) => handleIngredientChange(index, 'price', parseFloat(e.target.value) || 0)}
                            className="px-2 py-1 bg-gray-600/50 border border-purple-500/30 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
                            placeholder="Цена ₽"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* History */}
              <div className="mt-8">
                <h3 className="text-lg font-bold text-white mb-4">
                  История ({userTechCards.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {userTechCards.slice(0, 10).map((card, index) => (
                    <div
                      key={card.id}
                      onClick={() => handleSelectTechCard(card)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        currentTechCardId === card.id 
                          ? 'bg-purple-600/30 border border-purple-500'
                          : 'bg-gray-700/30 hover:bg-gray-700/50'
                      }`}
                    >
                      <div className="text-purple-200 font-medium text-sm">
                        {card.dish_name}
                      </div>
                      <div className="text-gray-400 text-xs">
                        {new Date(card.created_at).toLocaleDateString('ru-RU')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Tech Card Display */}
          <div className="lg:col-span-2">
            {techCard ? (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-white">
                    Технологическая карта
                  </h2>
                  <div className="flex space-x-3">
                    <button 
                      onClick={handlePrintTechCard}
                      className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                      📄 Экспорт в PDF
                    </button>
                  </div>
                </div>
                <div className="prose prose-invert max-w-none">
                  {formatTechCard(techCard)}
                </div>
              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-purple-500/20 text-center">
                <div className="text-purple-200 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-white mb-2">
                  Техкарта появится здесь
                </h3>
                <p className="text-gray-300">
                  Введите название блюда слева и нажмите "Создать техкарту"
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;