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

  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('');
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [recognition, setRecognition] = useState(null);

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    email: '',
    name: '',
    city: ''
  });

  useEffect(() => {
    fetchCities();
    initVoiceRecognition();
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

  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'ru-RU';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
        setVoiceStatus('Говорите название блюда...');
        setShowVoiceModal(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setDishName(transcript);
        setVoiceStatus(`Распознано: "${transcript}"`);
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 1500);
      };
      
      recognitionInstance.onerror = (event) => {
        setVoiceStatus('Ошибка распознавания. Попробуйте еще раз.');
        setTimeout(() => {
          setShowVoiceModal(false);
          setIsListening(false);
        }, 2000);
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
      };
      
      setRecognition(recognitionInstance);
    }
  };

  const startVoiceRecognition = () => {
    if (recognition) {
      recognition.start();
    } else {
      alert('Голосовое распознавание не поддерживается в вашем браузере');
    }
  };

  const stopVoiceRecognition = () => {
    if (recognition && isListening) {
      recognition.stop();
      setShowVoiceModal(false);
      setIsListening(false);
    }
  };

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
      fetchUserTechCards();
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
      fetchUserTechCards();
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
        headers: { 'Content-Type': 'application/json' }
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
    updateTechCardWithIngredients(newIngredients);
  };

  const updateTechCardWithIngredients = (newIngredients) => {
    const totalCost = newIngredients.reduce((sum, ing) => sum + (ing.price || 0), 0);
    const recommendedPrice = Math.round(totalCost * 3);
    
    let updatedContent = techCard;
    
    const ingredientsSection = newIngredients.map(ing => 
      `- ${ing.name} — ${ing.quantity} — ~${ing.price} ₽`
    ).join('\n');
    
    updatedContent = updatedContent.replace(
      /(\*\*Ингредиенты:\*\*\n\n)([\s\S]*?)(\n\n\*\*Пошаговый рецепт:\*\*)/,
      `$1${ingredientsSection}$3`
    );
    
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
          <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
          <style>
            * { font-family: 'Montserrat', sans-serif !important; }
            body { 
              line-height: 1.6; 
              margin: 40px; 
              background: white; 
              color: #1A1B23; 
            }
            h1 { 
              color: #8B5CF6; 
              font-size: 28px; 
              font-weight: 900;
              text-transform: uppercase;
              letter-spacing: 1.5px;
              text-align: center; 
              margin-bottom: 30px; 
              border-bottom: 3px solid #8B5CF6;
              padding-bottom: 15px;
            }
            h2 { 
              color: #1A1B23; 
              font-size: 18px; 
              font-weight: 800;
              text-transform: uppercase;
              letter-spacing: 0.8px;
              margin-top: 25px; 
              margin-bottom: 15px; 
              border-bottom: 2px solid #C084FC; 
              padding-bottom: 8px; 
            }
            .ingredients-table {
              width: 100%;
              border-collapse: collapse;
              margin: 20px 0;
              border: 2px solid #8B5CF6;
              border-radius: 8px;
            }
            .ingredients-table th {
              background: linear-gradient(135deg, #8B5CF6, #C084FC);
              color: white;
              font-weight: 800;
              font-size: 12px;
              text-transform: uppercase;
              padding: 12px;
            }
            .ingredients-table td {
              padding: 10px 12px;
              border-bottom: 1px solid #C084FC;
              font-weight: 500;
            }
            .cost-box {
              background: #F0FDF4;
              border: 2px solid #10B981;
              border-radius: 8px;
              padding: 15px;
              margin: 15px 0;
              font-weight: 700;
            }
            .step {
              background: #F8FAFC;
              border-left: 4px solid #8B5CF6;
              padding: 15px;
              margin: 10px 0;
              border-radius: 0 8px 8px 0;
            }
            .tip {
              background: #F3E8FF;
              border: 2px solid #C084FC;
              border-radius: 8px;
              padding: 12px;
              margin: 10px 0;
              font-style: italic;
            }
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <h1>📋 ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          <div>${formatTechCardForPrint(techCard)}</div>
          <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #64748B;">
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

  const formatTechCardForPrint = (content) => {
    return content.split('\n').map(line => {
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '');
        if (title.includes('Название:')) {
          return `<h1>${title.replace('Название:', '').trim()}</h1>`;
        }
        return `<h2>${title}</h2>`;
      }
      if (line.startsWith('💡') || line.startsWith('🔥') || line.startsWith('🌀')) {
        return `<div class="tip">${line}</div>`;
      }
      if (line.includes('Себестоимость:') || line.includes('Рекомендуемая цена')) {
        return `<div class="cost-box">${line}</div>`;
      }
      if (line.startsWith('- ')) {
        return `<p style="margin-left: 20px;">${line}</p>`;
      }
      if (line.match(/^\d+\./)) {
        return `<div class="step">${line}</div>`;
      }
      if (line.trim()) {
        return `<p>${line}</p>`;
      }
      return '<br>';
    }).join('');
  };

  const formatTechCard = (content) => {
    return content.split('\n').map((line, index) => {
      // Main title
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '');
        if (title.includes('Название:')) {
          return (
            <div key={index} className="fade-in-scale">
              <div className="tech-card-title">
                {title.replace('Название:', '').trim()}
              </div>
            </div>
          );
        }
        return (
          <div key={index} className="tech-card-section slide-in-bottom">
            {title}
          </div>
        );
      }
      
      // Ingredients table
      if (line.includes('**Ингредиенты:**') && !isEditing) {
        const ingredientLines = content.split('\n').slice(index + 1).filter(l => l.startsWith('- ') && l.includes(' — '));
        const tableRows = ingredientLines.map((ingLine, ingIndex) => {
          const parts = ingLine.replace('- ', '').split(' — ');
          if (parts.length >= 3) {
            return (
              <tr key={`ing-${ingIndex}`} className="slide-in-bottom" style={{animationDelay: `${ingIndex * 0.1}s`}}>
                <td className="font-semibold text-purple-200">{parts[0].trim()}</td>
                <td className="text-center text-gray-300">{parts[1].trim()}</td>
                <td className="text-right font-bold text-green-300">{parts[2].trim()}</td>
              </tr>
            );
          }
          return null;
        }).filter(Boolean);
        
        if (tableRows.length > 0) {
          return (
            <div key={index} className="my-8 slide-in-right">
              <div className="tech-card-section">ИНГРЕДИЕНТЫ</div>
              <div className="ingredients-table">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="text-left py-4 px-6">ИНГРЕДИЕНТ</th>
                      <th className="text-center py-4 px-6">КОЛИЧЕСТВО</th>
                      <th className="text-right py-4 px-6">ЦЕНА</th>
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
      
      // Skip processed ingredient lines
      if (line.startsWith('- ') && !isEditing && content.includes('**Ингредиенты:**')) {
        const isInIngredientsSection = content.split('\n').slice(0, index).some(l => l.includes('**Ингредиенты:**')) &&
                                      !content.split('\n').slice(0, index).some(l => l.includes('**Пошаговый рецепт:**'));
        if (isInIngredientsSection && line.includes(' — ')) {
          return null;
        }
      }
      
      // Cost information
      if (line.includes('Себестоимость:') || line.includes('Рекомендуемая цена')) {
        return (
          <div key={index} className="cost-highlight slide-in-left">
            <div className="font-bold text-lg text-green-100">{line}</div>
          </div>
        );
      }
      
      // Tips and advice
      if (line.startsWith('💡') || line.startsWith('🔥') || line.startsWith('🌀')) {
        return (
          <div key={index} className="tip-box slide-in-bottom">
            <div className="font-semibold text-purple-100">{line}</div>
          </div>
        );
      }
      
      // Food pairing
      if (line.startsWith('🍷') || line.startsWith('🍺') || line.startsWith('🍹')) {
        return (
          <div key={index} className="ml-6 mb-2 font-medium text-pink-200">
            {line}
          </div>
        );
      }
      
      // Sales script
      if (line.startsWith('💬')) {
        return (
          <div key={index} className="tip-box border-purple-400 bg-purple-900/20">
            <div className="font-semibold text-purple-200">{line}</div>
          </div>
        );
      }
      
      // Photography tips
      if (line.startsWith('📸')) {
        return (
          <div key={index} className="tip-box border-blue-400 bg-blue-900/20">
            <div className="font-medium text-blue-200">{line}</div>
          </div>
        );
      }
      
      // Menu tags
      if (line.startsWith('🏷️')) {
        return (
          <div key={index} className="font-medium text-yellow-300 mb-4">
            {line}
          </div>
        );
      }
      
      // Regular list items
      if (line.startsWith('- ')) {
        return (
          <div key={index} className="ml-6 mb-2 text-gray-300 font-medium">
            {line}
          </div>
        );
      }
      
      // Numbered steps
      if (line.match(/^\d+\./)) {
        return (
          <div key={index} className="step-card slide-in-bottom" style={{animationDelay: `${index * 0.05}s`}}>
            <div className="font-medium text-gray-200 leading-relaxed">{line}</div>
          </div>
        );
      }
      
      // Regular paragraphs
      if (line.trim()) {
        return (
          <div key={index} className="mb-3 text-gray-300 font-medium leading-relaxed">
            {line}
          </div>
        );
      }
      
      return <div key={index} className="mb-3"></div>;
    }).filter(Boolean);
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full filter blur-3xl"></div>
        </div>
        
        <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
          <div className="max-w-md w-full">
            <div className="text-center mb-12 slide-in-bottom">
              <div className="mb-8">
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center pulse-glow">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg"></div>
                  </div>
                </div>
              </div>
              <h1 className="heading-main slide-in-left">
                RECEPTOR
              </h1>
              <p className="text-selling mb-4 slide-in-right">
                AI-ПОМОЩНИК ДЛЯ ШЕФ-ПОВАРОВ
              </p>
              <p className="text-subtitle slide-in-bottom">
                Создавайте профессиональные технологические карты за секунды
              </p>
              
              {/* Selling Points */}
              <div className="mt-8 space-y-3">
                <div className="selling-point slide-in-left" style={{animationDelay: '0.2s'}}>
                  ЭКОНОМЬТЕ 2 ЧАСА НА КАЖДОЙ ТЕХКАРТЕ
                </div>
                <div className="selling-point slide-in-left" style={{animationDelay: '0.4s'}}>
                  ТОЧНЫЕ РАСЧЕТЫ ДО КОПЕЙКИ
                </div>
                <div className="selling-point slide-in-left" style={{animationDelay: '0.6s'}}>
                  ОТ ИДЕИ ДО ТЕХКАРТЫ ЗА 30 СЕКУНД
                </div>
              </div>
            </div>

            {!showRegistration ? (
              <div className="card-glass p-8 slide-in-bottom">
                <h2 className="heading-section text-center mb-8">
                  ДОБРО ПОЖАЛОВАТЬ!
                </h2>
                <button
                  onClick={() => setShowRegistration(true)}
                  className="w-full btn-primary"
                >
                  НАЧАТЬ РАБОТУ
                </button>
              </div>
            ) : (
              <div className="card-glass p-8 slide-in-scale">
                <h2 className="heading-section text-center mb-8">
                  РЕГИСТРАЦИЯ
                </h2>
                <form onSubmit={handleRegistration} className="space-y-6">
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      EMAIL
                    </label>
                    <input
                      type="email"
                      value={registrationData.email}
                      onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                      className="w-full input-modern"
                      placeholder="ваш@email.com"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      ИМЯ
                    </label>
                    <input
                      type="text"
                      value={registrationData.name}
                      onChange={(e) => setRegistrationData({...registrationData, name: e.target.value})}
                      className="w-full input-modern"
                      placeholder="Имя Фамилия"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                      ГОРОД
                    </label>
                    <select
                      value={registrationData.city}
                      onChange={(e) => setRegistrationData({...registrationData, city: e.target.value})}
                      className="w-full input-modern"
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
                    className="w-full btn-primary"
                  >
                    ЗАРЕГИСТРИРОВАТЬСЯ
                  </button>
                </form>
                <button
                  onClick={() => setShowRegistration(false)}
                  className="w-full mt-4 text-purple-300 hover:text-purple-200 text-sm font-semibold uppercase tracking-wide"
                >
                  НАЗАД
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-10 left-10 w-96 h-96 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full filter blur-3xl"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full filter blur-3xl"></div>
      </div>

      {/* Voice Recognition Modal */}
      {showVoiceModal && (
        <div className="voice-status fade-in-scale">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-purple-300 mb-4">ГОЛОСОВОЙ ВВОД</h3>
            <p className="text-gray-300 mb-4">{voiceStatus}</p>
            <div className="voice-waves">
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
              <div className="voice-wave"></div>
            </div>
            <button
              onClick={stopVoiceRecognition}
              className="btn-secondary mt-4"
            >
              ОСТАНОВИТЬ
            </button>
          </div>
        </div>
      )}

      <header className="relative z-10 card-glass border-0 border-b border-purple-400/30 rounded-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center slide-in-left">
              <h1 className="heading-card text-3xl">RECEPTOR</h1>
              <span className="ml-4 text-purple-300 font-semibold uppercase tracking-wide">AI для шеф-поваров</span>
            </div>
            <div className="flex items-center space-x-6 slide-in-right">
              <span className="text-gray-300 font-medium">
                <span className="text-purple-300 font-bold">{currentUser.name}</span>
                <span className="text-gray-400 ml-2">
                  ({cities.find(c => c.code === currentUser.city)?.name})
                </span>
              </span>
              <button
                onClick={handleLogout}
                className="text-purple-300 hover:text-purple-200 font-semibold uppercase tracking-wide transition-all duration-300"
              >
                ВЫЙТИ
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left Panel */}
          <div className="lg:col-span-1 slide-in-left">
            <div className="card-glass p-8">
              <h2 className="heading-card mb-6">
                СОЗДАТЬ ТЕХКАРТУ
              </h2>
              <form onSubmit={handleGenerateTechCard} className="space-y-6">
                <div>
                  <label className="block text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                    НАЗВАНИЕ БЛЮДА
                  </label>
                  <div className="voice-input-container">
                    <input
                      type="text"
                      value={dishName}
                      onChange={(e) => setDishName(e.target.value)}
                      placeholder="Например: Стейк с картофелем"
                      className="input-modern"
                      required
                    />
                    <button
                      type="button"
                      onClick={startVoiceRecognition}
                      className={`btn-voice ${isListening ? 'recording' : ''}`}
                      title="Голосовой ввод"
                    >
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className={`w-full btn-primary ${isGenerating ? 'loading-pulse' : ''}`}
                >
                  {isGenerating ? 'ГЕНЕРИРУЕТСЯ...' : 'СОЗДАТЬ ТЕХКАРТУ'}
                </button>
              </form>

              {/* AI Editing */}
              {techCard && (
                <div className="mt-8 border-t border-purple-400/30 pt-8 slide-in-bottom">
                  <h3 className="heading-card text-lg mb-6">
                    РЕДАКТИРОВАТЬ ЧЕРЕЗ AI
                  </h3>
                  <form onSubmit={handleEditWithAI} className="space-y-4">
                    <input
                      type="text"
                      value={editInstruction}
                      onChange={(e) => setEditInstruction(e.target.value)}
                      placeholder="Например: увеличить порцию в 2 раза"
                      className="w-full input-modern"
                    />
                    <button
                      type="submit"
                      disabled={isEditingAI || !editInstruction.trim()}
                      className={`w-full btn-secondary ${isEditingAI ? 'loading-pulse' : ''}`}
                    >
                      {isEditingAI ? 'РЕДАКТИРУЕТСЯ...' : 'ИЗМЕНИТЬ ЧЕРЕЗ AI'}
                    </button>
                  </form>
                  
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="w-full mt-4 btn-secondary"
                  >
                    {isEditing ? 'ЗАКРЫТЬ РЕДАКТОР' : 'РУЧНОЕ РЕДАКТИРОВАНИЕ'}
                  </button>
                </div>
              )}

              {/* Manual Editing */}
              {isEditing && ingredients.length > 0 && (
                <div className="mt-8 border-t border-purple-400/30 pt-8 slide-in-bottom">
                  <h3 className="heading-card text-lg mb-6">
                    ✏️ РЕДАКТИРОВАТЬ ИНГРЕДИЕНТЫ
                  </h3>
                  <div className="space-y-4 max-h-80 overflow-y-auto">
                    {ingredients.map((ingredient, index) => (
                      <div key={index} className="card-glass p-4">
                        <div className="text-purple-300 text-sm font-bold mb-3 uppercase tracking-wide">
                          {ingredient.name}
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <input
                            type="text"
                            value={ingredient.quantity}
                            onChange={(e) => handleIngredientChange(index, 'quantity', e.target.value)}
                            className="input-modern text-sm"
                            placeholder="Количество"
                          />
                          <input
                            type="number"
                            value={ingredient.price}
                            onChange={(e) => handleIngredientChange(index, 'price', parseFloat(e.target.value) || 0)}
                            className="input-modern text-sm"
                            placeholder="Цена ₽"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* History */}
              <div className="mt-10 slide-in-bottom">
                <h3 className="heading-card text-lg mb-6">
                  ИСТОРИЯ ({userTechCards.length})
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {userTechCards.slice(0, 10).map((card, index) => (
                    <div
                      key={card.id}
                      onClick={() => handleSelectTechCard(card)}
                      className={`history-item ${currentTechCardId === card.id ? 'active' : ''}`}
                      style={{animationDelay: `${index * 0.1}s`}}
                    >
                      <div className="font-bold text-purple-300 text-sm uppercase tracking-wide">
                        {card.dish_name}
                      </div>
                      <div className="text-gray-400 text-xs font-medium">
                        {new Date(card.created_at).toLocaleDateString('ru-RU')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-2 slide-in-right">
            {techCard ? (
              <div className="tech-card-container">
                <div className="flex justify-between items-center mb-8">
                  <h2 className="heading-section">
                    ТЕХНОЛОГИЧЕСКАЯ КАРТА
                  </h2>
                  <button 
                    onClick={handlePrintTechCard}
                    className="btn-success"
                  >
                    📄 ЭКСПОРТ В PDF
                  </button>
                </div>
                <div className="tech-card-content">
                  {formatTechCard(techCard)}
                </div>
              </div>
            ) : (
              <div className="card-glass p-12 text-center slide-in-scale">
                <div className="mb-8">
                  <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-400/30 to-pink-500/30 rounded-2xl flex items-center justify-center border-2 border-purple-400/30">
                    <svg className="w-12 h-12 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
                <h3 className="heading-card text-2xl mb-4">
                  ТЕХКАРТА ПОЯВИТСЯ ЗДЕСЬ
                </h3>
                <p className="text-subtitle">
                  Введите название блюда слева и нажмите <span className="text-purple-300 font-bold">"СОЗДАТЬ ТЕХКАРТУ"</span>
                </p>
                <div className="mt-8">
                  <div className="selling-point">
                    🎤 ПОПРОБУЙТЕ ГОЛОСОВОЙ ВВОД!
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;