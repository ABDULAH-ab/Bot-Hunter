import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

const Logo = ({ className = '', showText = true, size = 'default', useMUI = false }) => {
  const sizes = {
    small: { icon: 24, text: 'body1' },
    default: { icon: 32, text: 'h6' },
    large: { icon: 48, text: 'h4' },
  };

  const sizeClasses = sizes[size];

  const RobotIcon = ({ size }) => (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      style={{
        filter: 'drop-shadow(0 0 8px rgba(0, 217, 255, 0.6))',
      }}
    >
      {/* Robot Head Outline */}
      <rect
        x="6"
        y="8"
        width="28"
        height="24"
        rx="4"
        stroke="#00d9ff"
        strokeWidth="2"
        fill="none"
      />
      {/* Eyes */}
      <line
        x1="14"
        y1="18"
        x2="14"
        y2="22"
        stroke="#00d9ff"
        strokeWidth="2.5"
        strokeLinecap="round"
        style={{
          filter: 'drop-shadow(0 0 4px rgba(0, 217, 255, 0.8))',
        }}
      />
      <line
        x1="26"
        y1="18"
        x2="26"
        y2="22"
        stroke="#00d9ff"
        strokeWidth="2.5"
        strokeLinecap="round"
        style={{
          filter: 'drop-shadow(0 0 4px rgba(0, 217, 255, 0.8))',
        }}
      />
      {/* Antenna */}
      <path
        d="M 10 8 L 10 4"
        stroke="#00d9ff"
        strokeWidth="2"
        strokeLinecap="round"
        style={{
          filter: 'drop-shadow(0 0 4px rgba(0, 217, 255, 0.6))',
        }}
      />
      <circle
        cx="10"
        cy="2"
        r="1.5"
        fill="#00d9ff"
        style={{
          filter: 'drop-shadow(0 0 6px rgba(0, 217, 255, 0.8))',
        }}
      />
    </svg>
  );

  if (useMUI) {
    return (
      <Box
        component={Link}
        to="/"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          textDecoration: 'none',
          ...(className && className),
        }}
      >
        <RobotIcon size={sizeClasses.icon} />
        {showText && (
          <Typography
            variant={sizeClasses.text}
            sx={{
              fontFamily: 'monospace',
              fontWeight: 700,
            }}
          >
            <span style={{ color: '#00d9ff', textShadow: '0 0 8px rgba(0, 217, 255, 0.6)' }}>
              BOT
            </span>
            <span style={{ color: '#ffffff' }}>HUNTER</span>
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Link to="/" className={`flex items-center gap-2 ${className}`}>
      {/* Robot Icon */}
      <div className={`relative`} style={{ width: sizeClasses.icon, height: sizeClasses.icon }}>
        <RobotIcon size={sizeClasses.icon} />
      </div>
      
      {/* Text */}
      {showText && (
        <span className={`font-mono font-bold ${sizeClasses.text}`}>
          <span className="text-primary drop-shadow-[0_0_8px_rgba(0,217,255,0.6)]">BOT</span>
          <span className="text-white">HUNTER</span>
        </span>
      )}
    </Link>
  );
};

export default Logo;

