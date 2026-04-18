import { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { HiMoon, HiUser, HiHeart, HiSparkles, HiArrowsUpDown } from 'react-icons/hi2';
import { getData } from '../services/chat';

const COLORS = {
  protein: '#10a37f',
  carbs: '#f59e0b',
  fats: '#6366f1',
};

export default function InsightsView() {
  const sleepData = getData('sleep');
  const activityData = getData('activity');
  const stressData = getData('stress');
  const nutritionData = getData('nutrition');
  const heartRateData = getData('heartRate');
  const bloodPressureData = getData('bloodPressure');

  // Prepare chart data
  const sleepTrendData = sleepData.trend.map((value, index) => ({
    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index],
    hours: value,
  }));

  const nutritionChartData = [
    { name: 'Protein', value: nutritionData.protein, color: COLORS.protein },
    { name: 'Carbs', value: nutritionData.carbs, color: COLORS.carbs },
    { name: 'Fats', value: nutritionData.fats, color: COLORS.fats },
  ];

  const stressRadialData = [{ name: 'HRV', value: stressData.hrv, fill: '#10a37f' }];

  const progressPercent = (activityData.steps / activityData.goal) * 100;

  const heartRateTrendData = heartRateData.trend.map((value, index) => ({
    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index],
    bpm: value,
  }));

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="font-serif text-3xl text-text-main mb-2">
          Your Health Twin Insights
        </h1>
        <p className="text-sm text-text-muted">
          Synthesized from your wearables, lifestyle, and population baselines.
        </p>
      </div>

      {/* 2x3 Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Sleep Card */}
        <MetricCard
          title="RECOVERY (SLEEP)"
          icon={HiMoon}
          data={sleepData}
          isLive={sleepData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {sleepData.hours}
              </span>
              <span className="text-sm text-text-muted">hours avg</span>
            </div>
            <ResponsiveContainer width="100%" height={80}>
              <AreaChart data={sleepTrendData}>
                <defs>
                  <linearGradient id="sleepGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10a37f" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10a37f" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="hours"
                  stroke="#10a37f"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#sleepGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
            <AIInsight text="Your recovery improved by 10% this week" />
          </div>
        </MetricCard>

        {/* Activity Card */}
        <MetricCard
          title="ACTIVITY (STEPS)"
          icon={HiUser}
          data={activityData}
          isLive={activityData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {activityData.steps.toLocaleString()}
              </span>
              <span className="text-sm text-text-muted">/ {activityData.goal.toLocaleString()} goal</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-text-muted">
                <span>Progress</span>
                <span>{Math.round(progressPercent)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(progressPercent, 100)}%` }}
                />
              </div>
            </div>
            <AIInsight text="You're 1,500 steps from your daily goal" />
          </div>
        </MetricCard>

        {/* Stress Card */}
        <MetricCard
          title="WELLBEING (STRESS)"
          icon={HiHeart}
          data={stressData}
          isLive={stressData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {stressData.hrv}
              </span>
              <span className="text-sm text-text-muted">HRV score</span>
            </div>
            <div className="flex justify-center py-2">
              <ResponsiveContainer width={120} height={120}>
                <RadialBarChart cx="60" cy="60" innerRadius={40} outerRadius={50} data={stressRadialData}>
                  <RadialBar dataKey="value" cornerRadius={10} fill="#10a37f" />
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center">
              <span className="inline-block px-3 py-1 rounded-full bg-gray-100 text-xs font-medium text-text-muted">
                {stressData.level}
              </span>
            </div>
            <AIInsight text="Your HRV is above average for your age group" />
          </div>
        </MetricCard>

        {/* Nutrition Card */}
        <MetricCard
          title="NUTRITION (MEALS)"
          icon={HiSparkles}
          data={nutritionData}
          isLive={nutritionData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {nutritionData.meals}
              </span>
              <span className="text-sm text-text-muted">meals logged</span>
            </div>
            <div className="flex justify-center py-2">
              <ResponsiveContainer width={140} height={140}>
                <PieChart>
                  <Pie
                    data={nutritionChartData}
                    cx="70"
                    cy="70"
                    innerRadius={40}
                    outerRadius={60}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {nutritionChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 text-xs">
              {nutritionChartData.map((item) => (
                <div key={item.name} className="flex items-center gap-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-text-muted">{item.name}</span>
                </div>
              ))}
            </div>
            <AIInsight text="Protein intake is optimal for muscle recovery" />
          </div>
        </MetricCard>

        {/* Heart Rate Card */}
        <MetricCard
          title="HEART RATE"
          icon={HiHeart}
          data={heartRateData}
          isLive={heartRateData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {heartRateData.bpm}
              </span>
              <span className="text-sm text-text-muted">bpm avg</span>
            </div>
            <div className="text-xs text-text-muted">
              Resting: {heartRateData.resting} bpm
            </div>
            <ResponsiveContainer width="100%" height={80}>
              <LineChart data={heartRateTrendData}>
                <Line
                  type="monotone"
                  dataKey="bpm"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
            <AIInsight text="Your heart rate is within healthy range" />
          </div>
        </MetricCard>

        {/* Blood Pressure Card */}
        <MetricCard
          title="BLOOD PRESSURE"
          icon={HiArrowsUpDown}
          data={bloodPressureData}
          isLive={bloodPressureData.isLive}
        >
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-text-main">
                {bloodPressureData.systolic}/{bloodPressureData.diastolic}
              </span>
              <span className="text-sm text-text-muted">mmHg</span>
            </div>
            <div className="text-center">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                bloodPressureData.status === 'Normal' 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-amber-100 text-amber-700'
              }`}>
                {bloodPressureData.status}
              </span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-text-muted">
                <span>Systolic</span>
                <span className="font-medium text-text-main">{bloodPressureData.systolic}</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full"
                  style={{ width: `${(bloodPressureData.systolic / 140) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-text-muted">
                <span>Diastolic</span>
                <span className="font-medium text-text-main">{bloodPressureData.diastolic}</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${(bloodPressureData.diastolic / 90) * 100}%` }}
                />
              </div>
            </div>
            <AIInsight text="Blood pressure readings are optimal" />
          </div>
        </MetricCard>
      </div>
    </div>
  );
}

function MetricCard({ title, icon: Icon, data, isLive, children }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <Icon className="text-primary text-lg" />
          <h3 className="text-xs uppercase tracking-wider text-text-muted font-semibold">
            {title}
          </h3>
        </div>
        <div className="relative">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium cursor-help ${
              isLive
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-600'
            }`}
            onMouseEnter={() => !isLive && setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            {isLive ? 'Live' : 'Estimated'}
          </span>
          {!isLive && showTooltip && (
            <div className="absolute right-0 top-full mt-2 w-48 p-2 bg-gray-900 text-white text-[10px] rounded-lg shadow-lg z-10">
              Live sensor data unavailable; showing baseline estimate.
            </div>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

function AIInsight({ text }) {
  return (
    <div className="pt-3 border-t border-gray-100">
      <p className="text-xs italic text-text-muted flex items-start gap-1">
        <span className="text-primary font-medium">AI Insight:</span> {text}
      </p>
    </div>
  );
}
