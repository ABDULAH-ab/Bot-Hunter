import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, LogIn, UserPlus, Shield, LogOut, Search, User, X, Menu } from 'lucide-react';
import Button from './ui/button';
import Logo from './Logo';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  const [isVisible, setIsVisible] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const lastScrollYRef = useRef(0);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileMenuOpen]);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY < 10) {
        setIsVisible(true);
      } else if (currentScrollY > lastScrollYRef.current + 8) {
        setIsVisible(false);
        setMobileMenuOpen(false);
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
    setMobileMenuOpen(false);
    logout();
    navigate('/');
  };

  const handleNavigate = (path) => {
    setMobileMenuOpen(false);
    navigate(path);
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

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Button
                  variant="ghost"
                  onClick={() => handleNavigate('/home')}
                  className="gap-2"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Home
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => handleNavigate('/new-scan')}
                  className="gap-2"
                >
                  <Search className="h-4 w-4" />
                  New Scan
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => handleNavigate('/dashboard')}
                  className="gap-2"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Button>
                {user?.is_admin && (
                  <Button
                    variant="ghost"
                    onClick={() => handleNavigate('/admin')}
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
                        onError={(e) => {
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
                  onClick={() => handleNavigate('/login')}
                  className="gap-2"
                >
                  <LogIn className="h-4 w-4" />
                  Login
                </Button>
                <Button
                  variant="hero"
                  onClick={() => handleNavigate('/signup')}
                  className="gap-2"
                >
                  <UserPlus className="h-4 w-4" />
                  Get Started
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden flex items-center justify-center w-10 h-10 rounded-lg text-foreground hover:bg-accent transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>
        </div>

        {/* Mobile Menu Panel */}
        <div
          className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
            mobileMenuOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
          }`}
        >
          <div className="border-t border-border/50 bg-background/95 backdrop-blur-xl px-4 py-4 space-y-2">
            {isAuthenticated ? (
              <>
                {/* User info */}
                <div className="flex items-center gap-3 px-3 py-3 rounded-lg bg-primary/5 border border-primary/20 mb-3">
                  <div className="flex items-center justify-center w-9 h-9 rounded-full bg-primary/10 border border-primary/30 overflow-hidden flex-shrink-0">
                    {user?.profile_picture ? (
                      <img
                        src={user.profile_picture}
                        alt={user?.username || 'User'}
                        className="w-full h-full object-cover"
                        referrerPolicy="no-referrer"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    ) : (
                      <User className="h-4 w-4 text-primary" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground truncate">{user?.username}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleNavigate('/home')}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-foreground hover:bg-accent transition-colors text-left"
                >
                  <LayoutDashboard className="h-5 w-5 text-primary" />
                  <span className="font-medium">Home</span>
                </button>
                <button
                  onClick={() => handleNavigate('/new-scan')}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-foreground hover:bg-accent transition-colors text-left"
                >
                  <Search className="h-5 w-5 text-primary" />
                  <span className="font-medium">New Scan</span>
                </button>
                <button
                  onClick={() => handleNavigate('/dashboard')}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-foreground hover:bg-accent transition-colors text-left"
                >
                  <LayoutDashboard className="h-5 w-5 text-primary" />
                  <span className="font-medium">Dashboard</span>
                </button>
                {user?.is_admin && (
                  <button
                    onClick={() => handleNavigate('/admin')}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-foreground hover:bg-accent transition-colors text-left"
                  >
                    <Shield className="h-5 w-5 text-primary" />
                    <span className="font-medium">Admin</span>
                  </button>
                )}
                <div className="border-t border-border/50 mt-2 pt-2">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-destructive hover:bg-destructive/10 transition-colors text-left"
                  >
                    <LogOut className="h-5 w-5" />
                    <span className="font-medium">Logout</span>
                  </button>
                </div>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleNavigate('/login')}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-foreground hover:bg-accent transition-colors text-left"
                >
                  <LogIn className="h-5 w-5 text-primary" />
                  <span className="font-medium">Login</span>
                </button>
                <button
                  onClick={() => handleNavigate('/signup')}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors text-left"
                >
                  <UserPlus className="h-5 w-5" />
                  <span className="font-medium">Get Started</span>
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Backdrop overlay when mobile menu is open */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
    </>
  );
};

export default Navbar;


