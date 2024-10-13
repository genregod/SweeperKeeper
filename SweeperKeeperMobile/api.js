import axios from 'axios';

const API_URL = 'https://SweeperKeeper.YOURUSERNAME.repl.co'; // Replace YOURUSERNAME with your actual Replit username

const api = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // This is important for maintaining session cookies
});

export const login = async (username, password) => {
  try {
    const response = await api.post('/login', { username, password });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

export const getCasinos = async () => {
  try {
    const response = await api.get('/api/casinos');
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

export const getAccounts = async () => {
  try {
    const response = await api.get('/api/accounts');
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

export const claimCoins = async (accountId) => {
  try {
    const response = await api.get(`/claim_coins/${accountId}`);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};

export const getAnalytics = async () => {
  try {
    const response = await api.get('/analytics');
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : error.message;
  }
};
