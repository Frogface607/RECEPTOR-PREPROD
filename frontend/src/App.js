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
  const [editableIngredients, setEditableIngredients] = useState([]);
  const [isEditingIngredients, setIsEditingIngredients] = useState(false);
  const [editableSteps, setEditableSteps] = useState([]);
  const [isEditingSteps, setIsEditingSteps] = useState(false);

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

  // Enhanced tech card formatter
  const formatTechCard = (content) => {
    const lines = content.split('\n');
    const result = [];
    
    for (let index = 0; index < lines.length; index++) {
      const line = lines[index].trim();
      
      // Main title - FIXED to show dish name
      if (line.startsWith('**') && line.endsWith('**') && line.includes('Название')) {
        const title = line.replace(/\*\*/g, '').replace('Название:', '').trim();
        if (title) {
          result.push(
            <div key={index} className="text-center mb-8">
              <h1 className="text-4xl font-bold text-purple-300 mb-4 animate-pulse">{title}</h1>
            </div>
          );
        }
        continue;
      }
      
      // Section headers - clean format without stars
      if (line.startsWith('**') && line.endsWith('**')) {
        const title = line.replace(/\*\*/g, '').replace(':', '').trim();
        if (title && !title.includes('Название')) {
          result.push(
            <h2 key={index} className="text-2xl font-bold text-purple-400 mt-8 mb-4 border-b-2 border-purple-400 pb-2 uppercase tracking-wide">
              {title}
            </h2>
          );
        }
        continue;
      }
      
      // Ingredients section - create table
      if (line === 'Ингредиенты' || line.includes('Ингредиенты')) {
        // Find all ingredient lines after this header
        const ingredientLines = [];
        let nextIndex = index + 1;
        
        while (nextIndex < lines.length) {
          const nextLine = lines[nextIndex].trim();
          
          // Stop at next section header
          if (nextLine.startsWith('**') || 
              nextLine.includes('Пошаговый рецепт') || 
              nextLine.includes('Время:') ||
              nextLine.includes('Выход:') ||
              nextLine.includes('Себестоимость:')) {
            break;
          }
          
          // Collect ingredient lines
          if ((nextLine.startsWith('- ') && (nextLine.includes(' — ') || nextLine.includes(' - '))) ||
              (nextLine.includes(' — ') && nextLine.includes('₽'))) {
            ingredientLines.push(nextLine);
          }
          
          nextIndex++;
        }
        
        if (ingredientLines.length > 0) {
          const tableRows = ingredientLines.map((ingLine, ingIndex) => {
            // Handle both em dash (—) and regular dash (-)
            let parts = ingLine.replace('- ', '').split(' — ');
            if (parts.length < 3) {
              parts = ingLine.replace('- ', '').split(' - ');
            }
            
            if (parts.length >= 3) {
              return (
                <tr key={`ing-${ingIndex}`} className="hover:bg-gray-700/50 transition-colors">
                  <td className="font-semibold text-purple-200 py-3 px-4 border-b border-purple-400/30">{parts[0].trim()}</td>
                  <td className="text-center text-gray-300 py-3 px-4 border-b border-purple-400/30">{parts[1].trim()}</td>
                  <td className="text-right font-bold text-green-300 py-3 px-4 border-b border-purple-400/30">{parts[2].trim()}</td>
                </tr>
              );
            }
            return null;
          }).filter(Boolean);
          
          if (tableRows.length > 0) {
            result.push(
              <div key={index} className="my-8">
                <h2 className="text-2xl font-bold text-purple-400 mb-4 border-b-2 border-purple-400 pb-2 uppercase tracking-wide">
                  ИНГРЕДИЕНТЫ
                </h2>
                <div className="overflow-x-auto bg-gray-800/50 rounded-lg">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-gradient-to-r from-purple-600 to-purple-700">
                        <th className="text-left py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">ИНГРЕДИЕНТ</th>
                        <th className="text-center py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">КОЛИЧЕСТВО</th>
                        <th className="text-right py-4 px-4 text-white font-bold text-sm uppercase tracking-wide">ЦЕНА</th>
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
        continue;
      }
      
      // Skip ingredient lines that are already rendered in table
      if ((line.startsWith('- ') && (line.includes(' — ') || line.includes(' - '))) ||
          (line.includes(' — ') && line.includes('₽'))) {
        const previousLines = lines.slice(0, index);
        const hasIngredientHeader = previousLines.some(l => 
          l.includes('Ингредиенты') && !l.includes('Пошаговый рецепт')
        );
        
        if (hasIngredientHeader) {
          continue; // Skip as it's already rendered in table
        }
      }
      
      // Cost information with better formatting
      if (line.includes('Себестоимость') || line.includes('Рекомендуемая цена') || line.includes('По ингредиентам')) {
        result.push(
          <div key={index} className="my-6 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
            <div className="font-bold text-lg text-green-200">{line}</div>
          </div>
        );
        continue;
      }
      
      // КБЖУ information
      if (line.includes('КБЖУ') || line.includes('Калории')) {
        result.push(
          <div key={index} className="my-6 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg">
            <div className="font-bold text-blue-200">{line}</div>
          </div>
        );
        continue;
      }
      
      // List items - improved styling
      if (line.startsWith('- ') && !line.includes(' — ') && !line.includes(' - ')) {
        result.push(
          <div key={index} className="ml-6 mb-2 text-gray-300 flex items-start">
            <span className="text-purple-400 mr-3 mt-1 text-lg">•</span>
            <span>{line.replace('- ', '')}</span>
          </div>
        );
        continue;
      }
      
      // Numbered steps with better styling
      if (line.match(/^\d+\./)) {
        result.push(
          <div key={index} className="bg-gray-800/50 p-4 rounded-lg mb-4 border-l-4 border-purple-500 hover:bg-gray-800/70 transition-colors">
            <div className="font-medium text-gray-200 leading-relaxed">{line}</div>
          </div>
        );
        continue;
      }
      
      // Regular paragraphs
      if (line && !line.startsWith('─') && !line.startsWith('*')) {
        result.push(
          <p key={index} className="mb-3 text-gray-300 leading-relaxed">
            {line}
          </p>
        );
        continue;
      }
    }
    
    return result;
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

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, registrationData);
      setCurrentUser(response.data);
      localStorage.setItem('receptor_user', JSON.stringify(response.data));
      setShowRegistration(false);
      setRegistrationData({ email: '', name: '', city: '' });
    } catch (error) {
      alert('Ошибка регистрации. Попробуйте еще раз.');
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
    } catch (error) {
      console.error('Error generating tech card:', error);
      alert('Ошибка при генерации техкарты');
    } finally {
      setIsGenerating(false);
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
            @media print {
              body { margin: 20px; }
            }
          </style>
        </head>
        <body>
          <h1>ТЕХНОЛОГИЧЕСКАЯ КАРТА</h1>
          <div>${techCard.split('\n').map(line => {
            const cleanLine = line.replace(/\*\*/g, '');
            if (line.startsWith('**') && line.endsWith('**')) {
              if (line.includes('Название')) {
                return `<h1>${cleanLine.replace('Название:', '').trim()}</h1>`;
              }
              return `<h2>${cleanLine.replace(':', '')}</h2>`;
            }
            if (line.startsWith('- ')) {
              return `<p style="margin-left: 20px;">• ${line.replace('- ', '')}</p>`;
            }
            if (line.match(/^\d+\./)) {
              return `<div style="background: #F8FAFC; border-left: 4px solid #8B5CF6; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">${line}</div>`;
            }
            if (line.trim()) {
              return `<p>${line}</p>`;
            }
            return '<br>';
          }).join('')}</div>
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

  useEffect(() => {
    fetchCities();
    const savedUser = localStorage.getItem('receptor_user');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
    }
  }, []);

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black flex items-center justify-center p-4">
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-gray-700">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-purple-300 mb-2">RECEPTOR PRO</h1>
            <p className="text-gray-400">AI для создания техкарт</p>
          </div>

          {!showRegistration ? (
            <div className="space-y-6">
              <button
                onClick={() => setShowRegistration(true)}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                НАЧАТЬ РАБОТУ
              </button>
            </div>
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
          <div className="flex items-center space-x-6">
            <span className="text-purple-300 font-bold">{currentUser.name}</span>
            <button
              onClick={handleLogout}
              className="text-purple-300 hover:text-purple-200 font-semibold"
            >
              ВЫЙТИ
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left Panel */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700">
              <h2 className="text-2xl font-bold text-purple-300 mb-6">СОЗДАТЬ ТЕХКАРТУ</h2>
              <form onSubmit={handleGenerateTechCard} className="space-y-6">
                <textarea
                  value={dishName}
                  onChange={(e) => setDishName(e.target.value)}
                  placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none"
                  rows={5}
                  required
                />
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50"
                >
                  {isGenerating ? 'ГЕНЕРИРУЕТСЯ...' : 'СОЗДАТЬ ТЕХКАРТУ'}
                </button>
              </form>
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
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                    >
                      ЭКСПОРТ В PDF
                    </button>
                  </div>
                </div>
                <div className="prose prose-invert max-w-none">
                  {formatTechCard(techCard)}
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
    </div>
  );
}

export default App;