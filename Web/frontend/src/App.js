import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './context/AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Homepage from './pages/Homepage';
import NewScan from './pages/NewScan';
import AdminDashboard from './pages/AdminDashboard';
import ForgotPassword from './pages/ForgotPassword';
import Terms from './pages/Terms';
import Privacy from './pages/Privacy';
import PrivateRoute from './components/PrivateRoute';

// Google OAuth Client ID (get from Google Cloud Console)
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "your_client_id_here.apps.googleusercontent.com";

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d9ff',
      light: '#33e0ff',
      dark: '#00b8d9',
    },
    secondary: {
      main: '#00ff88',
      light: '#33ff9f',
      dark: '#00cc6a',
    },
    background: {
      default: '#0a0e27',
      paper: '#151b3d',
    },
    text: {
      primary: '#ffffff',
      secondary: '#a0aec0',
    },
    error: {
      main: '#ff4757',
    },
    warning: {
      main: '#ffa502',
    },
    success: {
      main: '#00ff88',
    },
    info: {
      main: '#00d9ff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 800,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 700,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 700,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 0 20px rgba(0, 217, 255, 0.4)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          background: 'linear-gradient(145deg, #151b3d 0%, #0f1530 100%)',
          border: '1px solid rgba(0, 217, 255, 0.1)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0, 217, 255, 0.1)',
          '&:hover': {
            border: '1px solid rgba(0, 217, 255, 0.3)',
            boxShadow: '0 8px 32px rgba(0, 217, 255, 0.2), 0 0 0 1px rgba(0, 217, 255, 0.3)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: 'rgba(21, 27, 61, 0.5)',
            '& fieldset': {
              borderColor: 'rgba(0, 217, 255, 0.2)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(0, 217, 255, 0.4)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00d9ff',
              boxShadow: '0 0 0 3px rgba(0, 217, 255, 0.1)',
            },
          },
          '& .MuiInputLabel-root': {
            color: '#a0aec0',
            '&.Mui-focused': {
              color: '#00d9ff',
            },
          },
        },
      },
    },
  },
});

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/terms" element={<Terms />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route
                path="/home"
                element={
                  <PrivateRoute>
                    <Homepage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/new-scan"
                element={
                  <PrivateRoute>
                    <NewScan />
                  </PrivateRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <PrivateRoute adminOnly={true}>
                    <AdminDashboard />
                  </PrivateRoute>
                }
              />
            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
