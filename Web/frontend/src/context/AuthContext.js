import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { TOKEN_EXPIRY_TIME, TOKEN_CHECK_INTERVAL, API_URL } from '../config/auth.config';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    // Check if token is expired before using it
    const tokenExpiry = localStorage.getItem('tokenExpiry');
    const now = new Date().getTime();
    
    if (token && tokenExpiry) {
      if (now > parseInt(tokenExpiry)) {
        // Token expired, logout
        console.log('Token expired, logging out...');
        logout();
        return;
      }
    }
    
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  // Periodic check for token expiration (every minute)
  useEffect(() => {
    if (!token) return;

    const checkTokenExpiration = () => {
      const tokenExpiry = localStorage.getItem('tokenExpiry');
      const now = new Date().getTime();
      
      if (tokenExpiry && now > parseInt(tokenExpiry)) {
        console.log('Token expired during session, logging out...');
        alert('Your session has expired. Please login again.');
        logout();
        window.location.href = '/login';
      }
    };

    // Check at configured interval
    const interval = setInterval(checkTokenExpiration, TOKEN_CHECK_INTERVAL);

    return () => clearInterval(interval);
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_URL}/auth/me`);
      setUser(response.data);
      // Store user data in localStorage for quick access
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        username,
        password,
      });
      const { access_token } = response.data;
      
      // Set token expiry time from config
      const expiryTime = new Date().getTime() + TOKEN_EXPIRY_TIME;
      
      setToken(access_token);
      localStorage.setItem('token', access_token);
      localStorage.setItem('tokenExpiry', expiryTime.toString());
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUser();
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };

  const signup = async (username, email, password) => {
    try {
      await axios.post(`${API_URL}/auth/register`, {
        username,
        email,
        password,
      });
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('tokenExpiry'); // Remove expiry timestamp
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

