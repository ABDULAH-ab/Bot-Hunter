import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, LogIn, UserPlus, Shield, LogOut, Search, User } from 'lucide-react';
import Button from './ui/button';
import Logo from './Logo';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const [isVisible, setIsVisible] = useState(true);
  const lastScrollYRef = useRef(0);

  // Debug: Log user data
  useEffect(() => {
    if (user) {
      console.log('=== NAVBAR DEBUG ===');
      console.log('Full user object:', user);
      console.log('Username:', user.username);
      console.log('Email:', user.email);
      console.log('Profile picture:', user.profile_picture);
      console.log('Auth provider:', user.auth_provider);
      console.log('Google ID:', user.google_id);
      console.log('===================');
    }
  }, [user]);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY < 10) {
        setIsVisible(true);
      } else if (currentScrollY > lastScrollYRef.current + 8) {
        setIsVisible(false);
      } else if (currentScrollY < lastScrollYRef.current - 8) {
        setIsVisible(true);
      }

      lastScrollYRef.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    handleScroll();

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <>
      <div className="h-16" aria-hidden="true" />
      <nav className={`fixed top-0 left-0 right-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl transition-transform duration-300 will-change-transform ${
        isVisible ? 'translate-y-0' : '-translate-y-full'
      }`}>
        <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Logo />

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/home')}
                  className="gap-2"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Home
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/new-scan')}
                  className="gap-2"
                >
                  <Search className="h-4 w-4" />
                  New Scan
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => navigate('/dashboard')}
                  className="gap-2"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Button>
                {user?.is_admin && (
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/admin')}
                    className="gap-2"
                  >
                    <Shield className="h-4 w-4" />
                    Admin
                  </Button>
                )}
                {/* Profile Icon */}
                <div className="relative group">
                  <button
                    className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 border-2 border-primary/30 hover:border-primary transition-all group-hover:shadow-[0_0_20px_rgba(0,217,255,0.3)] overflow-hidden"
                  >
                    {user?.profile_picture ? (
                      <img 
                        src={user.profile_picture} 
                        alt={user?.username || 'User'}
                        className="w-full h-full object-cover"
                        crossOrigin="anonymous"
                        referrerPolicy="no-referrer"
                        onLoad={() => console.log('✅ Profile image loaded successfully:', user.profile_picture)}
                        onError={(e) => {
                          console.error('❌ Image failed to load:', user.profile_picture);
                          console.error('Error event:', e);
                          // Replace with fallback icon
                          e.target.style.display = 'none';
                          const parent = e.target.parentElement;
                          if (parent && !parent.querySelector('svg')) {
                            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                            svg.setAttribute('width', '20');
                            svg.setAttribute('height', '20');
                            svg.setAttribute('viewBox', '0 0 24 24');
                            svg.setAttribute('fill', 'none');
                            svg.setAttribute('stroke', 'currentColor');
                            svg.setAttribute('stroke-width', '2');
                            svg.setAttribute('class', 'text-primary');
                            svg.innerHTML = '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>';
                            parent.appendChild(svg);
                          }
                        }}
                      />
                    ) : (
                      <User className="h-5 w-5 text-primary" />
                    )}
                  </button>
                  {/* Dropdown */}
                  <div className="absolute right-0 mt-2 w-48 py-2 bg-card border border-border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                    <div className="px-4 py-2 border-b border-border">
                      <p className="text-sm font-semibold text-foreground">{user?.username}</p>
                      <p className="text-xs text-muted-foreground">{user?.email}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm text-destructive hover:bg-accent transition-colors flex items-center gap-2"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate('/login')}
                  className="gap-2"
                >
                  <LogIn className="h-4 w-4" />
                  Login
                </Button>
                <Button
                  variant="hero"
                  onClick={() => navigate('/signup')}
                  className="gap-2"
                >
                  <UserPlus className="h-4 w-4" />
                  Get Started
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => {
              // Mobile menu toggle logic can be added here
            }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="4" x2="20" y1="12" y2="12" />
              <line x1="4" x2="20" y1="6" y2="6" />
              <line x1="4" x2="20" y1="18" y2="18" />
            </svg>
          </Button>
        </div>
        </div>
      </nav>
    </>
  );
};

export default Navbar;

