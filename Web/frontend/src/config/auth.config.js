// Authentication Configuration

// Token expiration time in milliseconds
// Current: 24 hours
// Options:
//   - 1 hour: 1 * 60 * 60 * 1000
//   - 6 hours: 6 * 60 * 60 * 1000
//   - 12 hours: 12 * 60 * 60 * 1000
//   - 24 hours: 24 * 60 * 60 * 1000
//   - 7 days: 7 * 24 * 60 * 60 * 1000
//   - 30 days: 30 * 24 * 60 * 60 * 1000

export const TOKEN_EXPIRY_TIME = 24 * 60 * 60 * 1000; // 24 hours

// Check interval for token expiration (in milliseconds)
// Current: 1 minute
export const TOKEN_CHECK_INTERVAL = 60000; // 1 minute

// API Base URL
export const API_URL = 'http://localhost:8000/api';
