import React from 'react'
import { useLocation, Link } from 'react-router-dom'
import { NAV_ITEMS } from '../../constants/routes'

// Simple icon components using Tailwind shapes
const IconHome = () => (
  <div className="w-5 h-5 border-2 border-current rounded-sm relative">
    <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-b-2 border-current border-l-transparent border-r-transparent"></div>
  </div>
)

const IconBuilding = () => (
  <div className="w-5 h-5 border-2 border-current rounded-sm">
    <div className="flex justify-center items-center h-full">
      <div className="w-2 h-2 border border-current"></div>
    </div>
  </div>
)

const IconMenu = () => (
  <div className="w-5 h-5 flex flex-col justify-center space-y-1">
    <div className="h-0.5 bg-current rounded"></div>
    <div className="h-0.5 bg-current rounded"></div>
    <div className="h-0.5 bg-current rounded"></div>
  </div>
)

const IconLibrary = () => (
  <div className="w-5 h-5 border-2 border-current rounded-sm relative">
    <div className="absolute inset-1 flex flex-col space-y-0.5">
      <div className="h-0.5 bg-current rounded"></div>
      <div className="h-0.5 bg-current rounded"></div>
    </div>
  </div>
)

const IconLab = () => (
  <div className="w-5 h-5 relative">
    <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3 h-3 border-2 border-current rounded-full"></div>
    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-2 h-2 border-2 border-current rounded-sm"></div>
  </div>
)

const IconPricing = () => (
  <div className="w-5 h-5 border-2 border-current rounded-sm relative">
    <div className="absolute inset-1 flex items-center justify-center">
      <div className="text-xs font-bold leading-none">₽</div>
    </div>
  </div>
)

const IconAnalytics = () => (
  <div className="w-5 h-5 relative">
    <div className="flex items-end justify-between h-full space-x-0.5">
      <div className="w-1 h-2 bg-current rounded-t"></div>
      <div className="w-1 h-3 bg-current rounded-t"></div>
      <div className="w-1 h-4 bg-current rounded-t"></div>
      <div className="w-1 h-1 bg-current rounded-t"></div>
    </div>
  </div>
)

const iconComponents = {
  home: IconHome,
  building: IconBuilding,
  menu: IconMenu,
  library: IconLibrary,
  lab: IconLab,
  pricing: IconPricing,
  analytics: IconAnalytics,
}

const Sidebar: React.FC = () => {
  const location = useLocation()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <nav className="flex-1 px-4 py-6 space-y-2">
        {NAV_ITEMS.map((item) => {
          const IconComponent = iconComponents[item.icon as keyof typeof iconComponents]
          const isActive = location.pathname === item.path
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={isActive ? 'nav-item-active' : 'nav-item-inactive'}
            >
              <IconComponent />
              <span className="ml-3">{item.name}</span>
            </Link>
          )
        })}
      </nav>
      
      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-200">
        <p className="text-body-xs text-gray-500 text-center">
          V3 Bootstrap
        </p>
      </div>
    </aside>
  )
}

export default Sidebar