import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

// Mock live data (simulating wearables API)
const liveData = {
  sleep: { hours: 7.2, trend: [6.5, 7.0, 6.8, 7.2, 7.5, 7.1, 7.2] },
  activity: { steps: 8432, goal: 10000 },
  stress: { hrv: 65, level: 'Moderate' },
  nutrition: { protein: 120, carbs: 250, fats: 65, meals: 3 },
  heartRate: { bpm: 72, resting: 68, trend: [70, 72, 71, 73, 72, 74, 72] },
  bloodPressure: { systolic: 118, diastolic: 76, status: 'Normal' },
};

// Population baselines (by age/gender demographics)
const populationBaselines = {
  sleep: { hours: 7.0, trend: [6.8, 6.9, 7.0, 7.0, 7.1, 7.0, 7.0] },
  activity: { steps: 7500, goal: 10000 },
  stress: { hrv: 55, level: 'Moderate' },
  nutrition: { protein: 100, carbs: 280, fats: 70, meals: 3 },
  heartRate: { bpm: 75, resting: 70, trend: [72, 74, 73, 75, 74, 76, 75] },
  bloodPressure: { systolic: 120, diastolic: 80, status: 'Normal' },
};

export function getData(metric) {
  const live = liveData[metric];
  const baseline = populationBaselines[metric];

  // If live data exists, return it with 'Live' indicator
  if (live && metric !== 'stress') {
    return { ...live, isLive: true };
  }

  // For stress, we have live data too
  if (live && metric === 'stress') {
    return { ...live, isLive: true };
  }

  // Return baseline estimate with 'Estimated' indicator
  return { ...baseline, isLive: false };
}

export async function sendChatMessage(message, userId = null) {
  const CHAT_API_BASE = 'http://localhost:8000/api/chat';
  const payload = { message };
  if (userId) {
    payload.user_id = userId;
  }
  const response = await axios.post(CHAT_API_BASE, payload);
  return response.data; // Returns { reply: "AI text", emotion: "detected_mood" }
}

export async function fetchInsights(userId = null) {
  const url = `${API_BASE}/user/insights`;
  const params = userId ? { user_id: userId } : {};
  const response = await axios.get(url, { params });
  return response.data;
}

export async function runSimulation(payload) {
  const response = await axios.post(`${API_BASE}/simulate`, payload);
  return response.data;
}

export async function fetchChatHistory(userId = null, source = null) {
  const url = `${API_BASE}/chat/history`;
  const params = userId ? { user_id: userId } : {};
  if (source) {
    params.source = source;
  }
  const response = await axios.get(url, { params });
  return response.data;
}
