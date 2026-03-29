import React, { useState, useEffect } from 'react';
import { X, Gift, Copy, Check, Users } from 'lucide-react';
import axios from 'axios';
import { API_URL, USER_ID } from '../config';
import { toast } from './Toast';

function ReferralModal({ isOpen, onClose }) {
  const [referralCode, setReferralCode] = useState('');
  const [inputCode, setInputCode] = useState('');
  const [stats, setStats] = useState(null);
  const [copied, setCopied] = useState(false);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    if (isOpen) loadReferralData();
  }, [isOpen]);

  const loadReferralData = async () => {
    try {
      const response = await axios.get(`${API_URL}/billing/referral/${USER_ID}`);
      setReferralCode(response.data.referral_code || '');
      setStats(response.data);
    } catch (error) {
      console.error('Error loading referral data:', error);
    }
  };

  const copyCode = async () => {
    await navigator.clipboard.writeText(referralCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast('Код скопирован!', 'success');
  };

  const applyCode = async () => {
    if (!inputCode.trim()) return;
    setApplying(true);
    try {
      const response = await axios.post(`${API_URL}/billing/referral/apply`, {
        user_id: USER_ID,
        code: inputCode.trim().toUpperCase(),
      });
      toast(response.data.message, 'success');
      setInputCode('');
      loadReferralData();
    } catch (error) {
      toast(error.response?.data?.detail || 'Ошибка при применении кода', 'error');
    } finally {
      setApplying(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <Gift className="w-6 h-6 text-emerald-400" />
            <h2 className="text-lg font-bold text-white">Реферальная программа</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded-lg text-gray-400">
            <X size={20} />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Your code */}
          <div>
            <p className="text-sm text-gray-400 mb-2">Ваш реферальный код</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white font-mono text-lg tracking-wider text-center">
                {referralCode || '...'}
              </div>
              <button
                onClick={copyCode}
                className="p-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors"
              >
                {copied ? <Check size={20} /> : <Copy size={20} />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Поделитесь кодом — вы оба получите 14 дней Pro бесплатно
            </p>
          </div>

          {/* Stats */}
          {stats && stats.total_referrals > 0 && (
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users size={16} className="text-emerald-400" />
                <span className="text-sm font-medium text-white">Ваша статистика</span>
              </div>
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-gray-400">Приглашено: </span>
                  <span className="text-white font-bold">{stats.total_referrals}</span>
                </div>
                <div>
                  <span className="text-gray-400">Бонус: </span>
                  <span className="text-emerald-400 font-bold">+{stats.bonus_days_earned} дней</span>
                </div>
              </div>
            </div>
          )}

          {/* Apply code */}
          <div>
            <p className="text-sm text-gray-400 mb-2">Есть код от друга?</p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={inputCode}
                onChange={(e) => setInputCode(e.target.value.toUpperCase())}
                placeholder="Введите код"
                maxLength={20}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 font-mono tracking-wider"
              />
              <button
                onClick={applyCode}
                disabled={!inputCode.trim() || applying}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg transition-colors font-medium text-sm"
              >
                {applying ? '...' : 'Применить'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReferralModal;
