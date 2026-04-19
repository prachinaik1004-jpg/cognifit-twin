import {
  HiChatBubbleLeftRight,
  HiChartBar,
  HiBeaker,
  HiDocumentText,
  HiClock,
  HiCog,
} from 'react-icons/hi2';

const navItems = [
  { id: 'Chat', label: 'Twin Chat', icon: HiChatBubbleLeftRight },
  { id: 'Insights', label: 'Insights', icon: HiChartBar },
  { id: 'What-If', label: 'What-If', icon: HiBeaker },
  { id: 'Summary', label: 'Summary', icon: HiDocumentText },
  { id: 'Settings', label: 'Settings', icon: HiCog },
];

const pastSimulations = [
  { id: 1, title: 'Sleep Impact on Memory', date: '2 hours ago', result: '+12%' },
  { id: 2, title: 'Diet Change Simulation', date: 'Yesterday', result: '+5%' },
  { id: 3, title: 'Exercise Frequency Test', date: '3 days ago', result: '+8%' },
  { id: 4, title: 'Stress Reduction Model', date: 'Last week', result: '+15%' },
];

export default function Sidebar({ currentView, onNavigate }) {
  const showSimHistory = currentView === 'What-If';

  return (
    <aside className="w-[260px] min-h-screen bg-white border-r border-gray-200 flex flex-col">
      <div className="px-4 pt-5 pb-3">
        <h1 className="text-lg font-semibold text-text-main tracking-tight">
          Cognitive Health Twin
        </h1>
        <p className="text-sm text-text-muted mt-0.5">Your digital health mirror</p>
      </div>

      <nav className="flex-1 px-2 space-y-0.5">
        {navItems.map(({ id, label, icon: Icon }) => {
          const isActive = currentView === id;
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-base transition-colors cursor-pointer
                ${
                  isActive
                    ? 'text-text-main bg-gray-100 font-medium'
                    : 'text-text-muted hover:bg-gray-50 hover:text-text-main font-normal'
                }`}
            >
              <Icon className="text-lg" />
              {label}
            </button>
          );
        })}
      </nav>

      {/* Past Simulations Section - Only shows when What-If is active */}
      {showSimHistory && (
        <div className="border-t border-gray-100">
          <div className="px-4 py-2.5">
            <div className="flex items-center gap-2 text-sm font-semibold text-text-main mb-2">
              <HiClock className="text-base" />
              Past Simulations
            </div>
            <div className="space-y-1">
              {pastSimulations.map((sim) => (
                <button
                  key={sim.id}
                  onClick={() => {}}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer group"
                >
                  <p className="text-sm text-text-main font-medium group-hover:text-primary transition-colors">
                    {sim.title}
                  </p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-text-muted">{sim.date}</span>
                    <span className="text-xs font-medium text-green-600">
                      {sim.result}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="px-4 py-3 border-t border-gray-100">
        <p className="text-xs text-text-muted">v0.1.0 - Prototype</p>
      </div>
    </aside>
  );
}
