import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export async function getAuthUrl(userId) {
  const response = await axios.get(`${API_BASE}/wearable/authorize`, {
    params: { user_id: userId }
  });
  return response.data;
}

export async function handleCallback(code, userId) {
  const response = await axios.post(`${API_BASE}/wearable/callback`, {
    code,
    user_id: userId
  });
  return response.data;
}

export async function syncWearableData(userId) {
  const response = await axios.post(`${API_BASE}/wearable/sync`, {
    user_id: userId
  });
  return response.data;
}

export async function getWearableData(userId, dataType = null, days = 7) {
  const params = { user_id: userId, days };
  if (dataType) {
    params.data_type = dataType;
  }
  const response = await axios.get(`${API_BASE}/wearable/data`, { params });
  return response.data;
}

export async function getWearableStatus(userId) {
  const response = await axios.get(`${API_BASE}/wearable/status`, {
    params: { user_id: userId }
  });
  return response.data;
}
