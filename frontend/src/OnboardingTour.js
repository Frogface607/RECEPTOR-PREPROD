import React from 'react';
import TourSystem from './components/TourSystem';
import tourConfigs from './tours/tourConfigs';

/**
 * 🎯 Главный онбординг RECEPTOR PRO
 * Wrapper для TourSystem с welcome tour
 */

const OnboardingTour = ({ onComplete, onSkip, isActive = false }) => {
  return (
    <TourSystem
      tourId="welcome"
      steps={tourConfigs.welcome}
      onComplete={onComplete}
      onSkip={onSkip}
      isActive={isActive}
      autoStart={false}
    />
  );
};

export default OnboardingTour;
