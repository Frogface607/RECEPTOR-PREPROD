import React, { useState } from 'react';
import { ChefHat, Users, Megaphone, BarChart3, UserPlus, Shield, Search, Zap, Crown, Lock } from 'lucide-react';
import { CATEGORIES, TOOLS, getToolsByCategory } from '../data/tools-catalog';

const ICON_MAP = {
  ChefHat, Users, Megaphone, BarChart3, UserPlus, Shield,
};

const COLOR_MAP = {
  emerald: { bg: 'bg-emerald-900/30', border: 'border-emerald-600/30', text: 'text-emerald-400', badge: 'bg-emerald-600' },
  blue:    { bg: 'bg-blue-900/30',    border: 'border-blue-600/30',    text: 'text-blue-400',    badge: 'bg-blue-600' },
  pink:    { bg: 'bg-pink-900/30',    border: 'border-pink-600/30',    text: 'text-pink-400',    badge: 'bg-pink-600' },
  purple:  { bg: 'bg-purple-900/30',  border: 'border-purple-600/30',  text: 'text-purple-400',  badge: 'bg-purple-600' },
  amber:   { bg: 'bg-amber-900/30',   border: 'border-amber-600/30',   text: 'text-amber-400',   badge: 'bg-amber-600' },
  cyan:    { bg: 'bg-cyan-900/30',    border: 'border-cyan-600/30',    text: 'text-cyan-400',    badge: 'bg-cyan-600' },
};

function ToolsCatalog({ onSelectTool }) {
  const [activeCategory, setActiveCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTools = searchQuery
    ? TOOLS.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : activeCategory
      ? getToolsByCategory(activeCategory)
      : TOOLS;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            <Zap className="inline w-8 h-8 text-emerald-400 mr-2 -mt-1" />
            AI-инструменты для ресторана
          </h1>
          <p className="text-gray-400">
            {TOOLS.length} инструментов для шефа, официантов, маркетинга и управления.
            Выбери → заполни → получи результат.
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-6 max-w-md mx-auto">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Найти инструмент..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setActiveCategory(null); }}
            className="w-full pl-11 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50"
          />
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-2 justify-center mb-8">
          <button
            onClick={() => { setActiveCategory(null); setSearchQuery(''); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              !activeCategory && !searchQuery
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            Все ({TOOLS.length})
          </button>
          {CATEGORIES.map(cat => {
            const Icon = ICON_MAP[cat.icon] || Zap;
            const count = getToolsByCategory(cat.id).length;
            const c = COLOR_MAP[cat.color];
            return (
              <button
                key={cat.id}
                onClick={() => { setActiveCategory(cat.id); setSearchQuery(''); }}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeCategory === cat.id
                    ? `${c.badge} text-white`
                    : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon size={14} />
                {cat.name} ({count})
              </button>
            );
          })}
        </div>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map(tool => {
            const cat = CATEGORIES.find(c => c.id === tool.category);
            const c = COLOR_MAP[cat?.color || 'emerald'];
            return (
              <button
                key={tool.id}
                onClick={() => onSelectTool(tool.id)}
                className={`text-left p-5 rounded-xl border transition-all hover:scale-[1.02] hover:shadow-lg ${c.bg} ${c.border} hover:border-opacity-60`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-10 h-10 rounded-lg ${c.badge} flex items-center justify-center`}>
                    <ChefHat size={20} className="text-white" />
                  </div>
                  {tool.free ? (
                    <span className="text-xs bg-emerald-600/20 text-emerald-400 px-2 py-0.5 rounded-full">Бесплатно</span>
                  ) : (
                    <Lock size={14} className="text-gray-500" />
                  )}
                </div>
                <h3 className="text-white font-semibold mb-1">{tool.name}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{tool.description}</p>
              </button>
            );
          })}
        </div>

        {filteredTools.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Ничего не найдено. Попробуйте другой запрос.
          </div>
        )}
      </div>
    </div>
  );
}

export default ToolsCatalog;
