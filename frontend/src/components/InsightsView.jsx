import { useState, useEffect } from 'react';
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
import { getData, fetchInsights } from '../services/chat';
import { getWearableData } from '../services/wearable';

const COLORS = {
  protein: '#10a37f',
  carbs: '#f59e0b',
  fats: '#6366f1',
};

export default function InsightsView({ user }) {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [wearableData, setWearableData] = useState({
    steps: [],
    heartRate: [],
    sleep: []
  });

  useEffect(() => {
    async function loadInsights() {
      try {
        const data = await fetchInsights(user?.id);
        setInsights(data);
      } catch (error) {
        console.error('Failed to fetch insights:', error);
      } finally {
        setLoading(false);
      }
    }
    loadInsights();
  }, [user?.id]);

  useEffect(() => {
    async function loadWearableData() {
      try {
        const [stepsRes, heartRateRes, sleepRes] = await Promise.all([
          getWearableData(user?.id, 'steps', 7),
          getWearableData(user?.id, 'heart_rate', 7),
          getWearableData(user?.id, 'sleep', 7),
        ]);
        console.log('Wearable API steps response:', JSON.stringify(stepsRes, null, 2));
        console.log('Wearable API heart rate response:', JSON.stringify(heartRateRes, null, 2));
        console.log('Wearable API sleep response:', JSON.stringify(sleepRes, null, 2));
        
        // Parse data - handle both {data: [...]} and direct array
        const stepsArr = stepsRes?.data || stepsRes || [];
        const hrArr = heartRateRes?.data || heartRateRes || [];
        const sleepArr = sleepRes?.data || sleepRes || [];
        
        // Parse value field - could be object or string
        const parseValue = (item) => {
          let val = item.value;
          if (typeof val === 'string') {
            try { val = JSON.parse(val); } catch(e) { val = {}; }
          }
          return val;
        };
        
        setWearableData({
          steps: stepsArr.map(item => ({ ...item, value: parseValue(item) })),
          heartRate: hrArr.map(item => ({ ...item, value: parseValue(item) })),
          sleep: sleepArr.map(item => ({ ...item, value: parseValue(item) }))
        });
      } catch (error) {
        console.error('Failed to fetch wearable data:', error);
      }
    }
    loadWearableData();
  }, [user?.id]);

  const hasLiveData = wearableData.steps.length > 0 || wearableData.heartRate.length > 0 || wearableData.sleep.length > 0;

  // Use real wearable data if available, otherwise fall back to mock
  const sleepData = wearableData.sleep.length > 0 
    ? { hours: wearableData.sleep[0]?.value?.hours || 7.2, trend: wearableData.sleep.map(d => d.value?.hours || 7), isLive: true }
    : insights?.sleep || getData('sleep');
  const activityData = wearableData.steps.length > 0
    ? { steps: wearableData.steps[0]?.value?.steps || 8432, goal: 10000, isLive: true }
    : insights?.activity || getData('activity');
  const stressData = insights?.stress || getData('stress');
  const nutritionData = insights?.nutrition || getData('nutrition');
  const heartRateData = wearableData.heartRate.length > 0
    ? { bpm: wearableData.heartRate[0]?.value?.bpm || 72, resting: 68, trend: wearableData.heartRate.map(d => d.value?.bpm || 72), isLive: true }
    : insights?.vitals
    ? { bpm: insights.vitals.heart_rate, resting: insights.vitals.resting_hr, trend: [70, 72, 71, 73, 72, 74, 72], isLive: true }
    : getData('heartRate');

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
        <div className="flex items-center gap-3 mb-2">
          <h1 className="font-serif text-3xl text-text-main">
            Your Health Twin Insights
          </h1>
          {hasLiveData ? (
            <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">Live Data</span>
          ) : (
            <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded-full">Mock Data</span>
          )}
        </div>
        <p className="text-sm text-text-muted">
          {insights ? `Personalized for ${insights.user?.name || 'you'}` : 'Synthesized from your wearables, lifestyle, and population baselines.'}
        </p>
      </div>

      {/* Risk Scores - removed, available in What-If simulator */}

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
