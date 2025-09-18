// Temporary simple version for compilation
export const useFeatureAccess = () => ({
  canUse: () => true,
  canUsePro: () => false,
  requiresPro: () => false,
  showUpgradeModal: () => false
})

export default useFeatureAccess