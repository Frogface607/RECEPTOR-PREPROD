import React from 'react';
import { Zap, Crown, Gift } from 'lucide-react';

/**
 * Показывает оставшиеся сообщения и кнопку апгрейда.
 * Появляется когда messages_remaining <= 3 или при paywall.
 */
function PaywallBanner({ plan, messagesRemaining, messagesLimit, onUpgrade, onReferral }) {
  if (!plan || plan === 'pro' || plan === 'enterprise') return null;
  if (messagesLimit === -1) return null; // unlimited

  const isBlocked = messagesRemaining <= 0;
  const isWarning = messagesRemaining > 0 && messagesRemaining <= 3;

  if (!isBlocked && !isWarning) return null;

  return (
    <div className={`mx-auto max-w-3xl px-4 py-3 rounded-xl border transition-all ${
      isBlocked
        ? 'bg-red-900/20 border-red-500/30'
        : 'bg-amber-900/20 border-amber-500/30'
    }`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isBlocked ? (
            <Crown className="w-5 h-5 text-amber-400 flex-shrink-0" />
          ) : (
            <Zap className="w-5 h-5 text-amber-400 flex-shrink-0" />
          )}
          <div>
            <p className={`text-sm font-medium ${isBlocked ? 'text-red-300' : 'text-amber-300'}`}>
              {isBlocked
                ? 'Лимит сообщений на сегодня исчерпан'
                : `Осталось ${messagesRemaining} из ${messagesLimit} сообщений на сегодня`
              }
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Перейдите на Pro для безлимитного общения с AI
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onReferral}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-emerald-400 border border-emerald-600/30 rounded-lg transition-colors"
          >
            <Gift size={14} />
            +14 дней бесплатно
          </button>
          <button
            onClick={onUpgrade}
            className="flex items-center gap-1.5 px-4 py-1.5 text-sm bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white rounded-lg transition-all shadow-lg shadow-emerald-500/20 font-medium"
          >
            <Crown size={14} />
            Pro за 6 990₽/мес
          </button>
        </div>
      </div>
    </div>
  );
}

export default PaywallBanner;
