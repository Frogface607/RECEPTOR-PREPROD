import React, { useState } from 'react';

const TechCardConstructor = ({
  dishName = '',
  onGenerate,
  isGenerating = false,
  showInstructions = false,
  onToggleInstructions,
  onVoiceInput,
  isListening = false
}) => {
  const [localDishName, setLocalDishName] = useState(dishName);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (localDishName.trim() && onGenerate) {
      onGenerate(localDishName.trim());
    }
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-4 sm:p-8 border border-gray-700 space-y-6 sm:space-y-8">
      <div>
        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <h2 className="text-xl sm:text-2xl font-semibold text-gray-200">СОЗДАТЬ ТЕХКАРТУ</h2>
          <button
            onClick={() => window.startTour_createTechcard && window.startTour_createTechcard()}
            className="text-gray-400 hover:text-gray-300 transition-colors text-sm font-medium"
            title="Показать тур: как создать техкарту"
          >
            Помощь
          </button>
        </div>
        
        {/* Instructions */}
        {showInstructions !== undefined && (
          <div className="mb-4 sm:mb-6">
            <div 
              className="flex items-center space-x-2 mb-3 sm:mb-4 cursor-pointer" 
              onClick={onToggleInstructions}
            >
              <span className="text-base sm:text-lg font-bold text-purple-300">КАК ПОЛЬЗОВАТЬСЯ</span>
              <span className="text-purple-300 text-lg sm:text-xl">{showInstructions ? '▼' : '▶'}</span>
            </div>
            {showInstructions && (
              <div className="bg-gradient-to-r from-purple-900/20 to-pink-900/20 rounded-xl p-4 sm:p-6 border border-purple-400/30 space-y-3 sm:space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:gap-6">
                  <div>
                    <h4 className="text-purple-300 font-bold mb-3 text-sm sm:text-base">СОЗДАНИЕ ТЕХКАРТЫ</h4>
                    <div className="space-y-2 text-xs sm:text-sm text-gray-300">
                      <p>• <strong>Пишите максимально подробно</strong> - чем точнее опишете, тем лучше результат</p>
                      <p>• <strong>Укажите количество порций</strong> - например "на 4 порции"</p>
                      <p>• <strong>Добавьте особенности</strong> - "средней прожарки", "с хрустящей корочкой"</p>
                      <p>• <strong>Голосовой ввод</strong> - нажмите кнопку микрофона для диктовки блюда</p>
                      <p className="text-purple-200">💡 <em>Пример: "Стейк из говядины на 4 порции, средней прожарки, общий выход 800г"</em></p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
          <div>
            <label className="block text-purple-300 text-sm font-bold mb-2 sm:mb-3 uppercase tracking-wide">
              НАЗВАНИЕ БЛЮДА
            </label>
            <div className="relative">
              <textarea
                value={localDishName}
                onChange={(e) => setLocalDishName(e.target.value)}
                placeholder="Опишите блюдо подробно. Например: Стейк из говядины с картофельным пюре и грибным соусом"
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-purple-500 outline-none min-h-[120px] resize-none text-sm sm:text-base"
                rows={5}
                required
                disabled={isGenerating}
              />
              {onVoiceInput && (
                <button
                  type="button"
                  onClick={onVoiceInput}
                  disabled={isGenerating}
                  className={`absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-300 ${
                    isListening 
                      ? 'bg-red-600 hover:bg-red-700 animate-pulse shadow-lg shadow-red-500/50' 
                      : 'bg-purple-600 hover:bg-purple-700'
                  } text-white w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center`}
                  title={isListening ? "Остановить запись" : "Голосовой ввод"}
                >
                  {isListening ? (
                    <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 0 1 5 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              )}
            </div>
          </div>
          <button
            type="submit"
            disabled={!localDishName.trim() || isGenerating}
            className={`w-full ${isGenerating ? 'bg-gray-600 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'} text-white font-semibold py-3 sm:py-4 px-6 rounded-lg transition-colors flex items-center justify-center text-sm sm:text-base min-h-[48px] sm:min-h-[56px]`}
            title="Создать профессиональную техническую карту с ингредиентами и процессом приготовления"
          >
            {isGenerating ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 sm:h-5 sm:w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                СОЗДАЮ РЕЦЕПТ...
              </>
            ) : 'СОЗДАТЬ ТЕХКАРТУ'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TechCardConstructor;

