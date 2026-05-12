import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, 
  Users, 
  TrendingUp, 
  Database, 
  Search, 
  Edit, 
  Trash2, 
  RefreshCw,
  CheckCircle,
  XCircle,
  UserCog,
  Activity,
  X
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Button from '../components/ui/button';
import Card from '../components/ui/card';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [userStats, setUserStats] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    checkAdminAccess();
  }, []);

  const checkAdminAccess = async () => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      navigate('/login');
      return;
    }

    // Fetch fresh user data from server to check admin status
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        
        if (!userData.is_admin) {
          setError('Admin access required. Redirecting...');
          setTimeout(() => navigate('/dashboard'), 2000);
        } else {
          // User is admin, fetch all data
          fetchAllData();
        }
      } else {
        setError('Failed to verify admin status');
        setTimeout(() => navigate('/login'), 2000);
      }
    } catch (err) {
      console.error('Admin check failed:', err);
      setError('Failed to verify admin status');
      setTimeout(() => navigate('/login'), 2000);
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchUsers(),
        fetchUserStats(),
        fetchSystemStats(),
        fetchRecentActivity()
      ]);
    } catch (err) {
      setError('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://localhost:8000/api/admin/users?limit=100', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      } else if (response.status === 403) {
        setError('Admin access required');
        setTimeout(() => navigate('/dashboard'), 2000);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchUserStats = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://localhost:8000/api/admin/stats/users', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch user stats:', error);
    }
  };

  const fetchSystemStats = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://localhost:8000/api/admin/stats/system', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch system stats:', error);
    }
  };

  const fetchRecentActivity = async () => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch('http://localhost:8000/api/admin/recent-activity', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRecentActivity(data.recent_users);
      }
    } catch (error) {
      console.error('Failed to fetch recent activity:', error);
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser({
      ...user,
      is_admin: user.is_admin || false,
      is_active: user.is_active !== false
    });
    setEditDialogOpen(true);
  };

  const handleUpdateUser = async () => {
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`http://localhost:8000/api/admin/users/${selectedUser._id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          is_admin: selectedUser.is_admin,
          is_active: selectedUser.is_active
        })
      });

      if (response.ok) {
        setSuccess('User updated successfully');
        setEditDialogOpen(false);
        fetchAllData();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update user');
      }
    } catch (err) {
      setError('Failed to update user');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) {
      return;
    }

    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`http://localhost:8000/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSuccess('User deactivated successfully');
        fetchAllData();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError('Failed to deactivate user');
      }
    } catch (err) {
      setError('Failed to deactivate user');
    }
  };

  const filteredUsers = users.filter(user => 
    user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="flex items-center justify-center min-h-[80vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-primary flex items-center gap-3 mb-2">
              <Shield className="h-10 w-10" />
              Admin Dashboard
            </h1>
            <p className="text-muted-foreground">
              Manage users, view statistics, and monitor system health
            </p>
          </div>
          <Button
            variant="outline"
            onClick={fetchAllData}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex justify-between items-center">
            <span className="text-destructive">{error}</span>
            <button onClick={() => setError('')} className="text-destructive hover:text-destructive/80">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex justify-between items-center">
            <span className="text-green-500">{success}</span>
            <button onClick={() => setSuccess('')} className="text-green-500 hover:text-green-500/80">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Users */}
          <Card className="bg-gradient-to-br from-purple-600 to-purple-800 border-purple-500/20">
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-200 text-sm mb-1">Total Users</p>
                  <h3 className="text-4xl font-bold text-white">
                    {userStats?.total_users || 0}
                  </h3>
                </div>
                <Users className="h-12 w-12 text-purple-200/60" />
              </div>
            </Card.Content>
          </Card>

          {/* Admin Users */}
          <Card className="bg-gradient-to-br from-pink-600 to-rose-800 border-pink-500/20">
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-pink-200 text-sm mb-1">Admin Users</p>
                  <h3 className="text-4xl font-bold text-white">
                    {userStats?.admin_users || 0}
                  </h3>
                </div>
                <Shield className="h-12 w-12 text-pink-200/60" />
              </div>
            </Card.Content>
          </Card>

          {/* New Users (24h) */}
          <Card className="bg-gradient-to-br from-cyan-600 to-blue-800 border-cyan-500/20">
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-cyan-200 text-sm mb-1">New (24h)</p>
                  <h3 className="text-4xl font-bold text-white">
                    {userStats?.users_last_24h || 0}
                  </h3>
                </div>
                <TrendingUp className="h-12 w-12 text-cyan-200/60" />
              </div>
            </Card.Content>
          </Card>

          {/* Database Size */}
          <Card className="bg-gradient-to-br from-green-600 to-teal-800 border-green-500/20">
            <Card.Content className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-200 text-sm mb-1">Database Size</p>
                  <h3 className="text-2xl font-bold text-white">
                    {systemStats?.database_size || '0 MB'}
                  </h3>
                </div>
                <Database className="h-12 w-12 text-green-200/60" />
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* User Management Section */}
        <Card className="mb-8">
          <Card.Content className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-foreground">User Management</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 w-80"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Username</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Auth</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-muted-foreground">Status</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-muted-foreground">Role</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Created</th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user._id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                      <td className="py-3 px-4 text-sm text-foreground">{user.username}</td>
                      <td className="py-3 px-4 text-sm text-foreground">{user.email}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          user.auth_provider === 'google' 
                            ? 'bg-primary/20 text-primary' 
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {user.auth_provider === 'google' ? 'Google' : 'Email'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {user.is_active !== false ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-500">
                            <CheckCircle className="h-3 w-3" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-destructive/20 text-destructive">
                            <XCircle className="h-3 w-3" />
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {user.is_admin ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-secondary/20 text-secondary">
                            <Shield className="h-3 w-3" />
                            Admin
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted/50 text-muted-foreground border border-border">
                            User
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleEditUser(user)}
                            className="p-1 hover:bg-primary/20 rounded transition-colors"
                          >
                            <Edit className="h-4 w-4 text-primary" />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user._id)}
                            className="p-1 hover:bg-destructive/20 rounded transition-colors"
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card.Content>
        </Card>

        {/* Recent Activity */}
        <Card>
          <Card.Content className="p-6">
            <h2 className="text-2xl font-bold text-foreground mb-6 flex items-center gap-2">
              <Activity className="h-6 w-6" />
              Recent User Activity
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Username</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Auth Provider</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {recentActivity.map((user) => (
                    <tr key={user._id} className="border-b border-border/50">
                      <td className="py-3 px-4 text-sm text-foreground">{user.username}</td>
                      <td className="py-3 px-4 text-sm text-foreground">{user.email}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          user.auth_provider === 'google' 
                            ? 'bg-primary/20 text-primary' 
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {user.auth_provider === 'google' ? 'Google' : 'Email'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card.Content>
        </Card>
      </div>

      {/* Edit User Modal */}
      {editDialogOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-foreground">Edit User</h3>
              <button
                onClick={() => setEditDialogOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {selectedUser && (
              <div>
                <div className="mb-4 space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Username: <span className="font-semibold text-foreground">{selectedUser.username}</span>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Email: <span className="font-semibold text-foreground">{selectedUser.email}</span>
                  </p>
                </div>

                <div className="border-t border-border my-4"></div>

                <div className="space-y-4">
                  <label className="flex items-center justify-between p-3 bg-accent/30 rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                    <span className="text-sm font-medium text-foreground">Active User</span>
                    <input
                      type="checkbox"
                      checked={selectedUser.is_active}
                      onChange={(e) => setSelectedUser({...selectedUser, is_active: e.target.checked})}
                      className="w-5 h-5 rounded border-border text-green-500 focus:ring-green-500"
                    />
                  </label>

                  <label className="flex items-center justify-between p-3 bg-accent/30 rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                    <span className="text-sm font-medium text-foreground">Admin Privileges</span>
                    <input
                      type="checkbox"
                      checked={selectedUser.is_admin}
                      onChange={(e) => setSelectedUser({...selectedUser, is_admin: e.target.checked})}
                      className="w-5 h-5 rounded border-border text-secondary focus:ring-secondary"
                    />
                  </label>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button
                    variant="outline"
                    onClick={() => setEditDialogOpen(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleUpdateUser}
                    className="flex-1"
                  >
                    Save Changes
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
