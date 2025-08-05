import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import { AutoAwesome, Psychology, TrendingUp } from '@mui/icons-material';

interface LoadingAnimationProps {
  message?: string;
  stage?: 'analyzing' | 'processing' | 'generating' | 'finalizing';
}

export const LoadingAnimation: React.FC<LoadingAnimationProps> = ({
  message = 'Generating prediction...',
  stage = 'processing'
}) => {
  const getStageIcon = () => {
    switch (stage) {
      case 'analyzing':
        return <Psychology sx={{ fontSize: 32, color: 'primary.main' }} />;
      case 'processing':
        return <AutoAwesome sx={{ fontSize: 32, color: 'secondary.main' }} />;
      case 'generating':
        return <TrendingUp sx={{ fontSize: 32, color: 'success.main' }} />;
      case 'finalizing':
        return <AutoAwesome sx={{ fontSize: 32, color: 'info.main' }} />;
      default:
        return <AutoAwesome sx={{ fontSize: 32, color: 'primary.main' }} />;
    }
  };

  const getStageMessage = () => {
    switch (stage) {
      case 'analyzing':
        return 'Analyzing player statistics...';
      case 'processing':
        return 'Processing match data...';
      case 'generating':
        return 'Generating AI prediction...';
      case 'finalizing':
        return 'Finalizing results...';
      default:
        return message;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        px: 4,
        minHeight: 200,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background Animation */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at center, rgba(63, 81, 181, 0.1) 0%, transparent 70%)',
          animation: 'pulse 2s ease-in-out infinite',
          '@keyframes pulse': {
            '0%': {
              transform: 'scale(1)',
              opacity: 0.5,
            },
            '50%': {
              transform: 'scale(1.1)',
              opacity: 0.8,
            },
            '100%': {
              transform: 'scale(1)',
              opacity: 0.5,
            },
          },
        }}
      />

      {/* Main Loading Icon */}
      <Box
        sx={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3,
          zIndex: 2,
        }}
      >
        <CircularProgress
          size={80}
          thickness={2}
          sx={{
            color: 'primary.main',
            position: 'absolute',
            animation: 'spin 2s linear infinite',
            '@keyframes spin': {
              '0%': { transform: 'rotate(0deg)' },
              '100%': { transform: 'rotate(360deg)' },
            },
          }}
        />
        <Box
          sx={{
            animation: 'iconFloat 2s ease-in-out infinite',
            '@keyframes iconFloat': {
              '0%': {
                transform: 'translateY(0px) scale(1)',
              },
              '50%': {
                transform: 'translateY(-8px) scale(1.1)',
              },
              '100%': {
                transform: 'translateY(0px) scale(1)',
              },
            },
          }}
        >
          {getStageIcon()}
        </Box>
      </Box>

      {/* Stage Message */}
      <Typography
        variant="h6"
        sx={{
          fontWeight: 600,
          mb: 1,
          textAlign: 'center',
          position: 'relative',
          zIndex: 2,
          animation: 'fadeInOut 2s ease-in-out infinite',
          '@keyframes fadeInOut': {
            '0%': { opacity: 0.7 },
            '50%': { opacity: 1 },
            '100%': { opacity: 0.7 },
          },
        }}
      >
        {getStageMessage()}
      </Typography>

      {/* Progress Dots */}
      <Box
        sx={{
          display: 'flex',
          gap: 0.5,
          mb: 2,
          position: 'relative',
          zIndex: 2,
        }}
      >
        {[0, 1, 2].map((index) => (
          <Box
            key={index}
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'primary.main',
              animation: `dotBounce 1.4s ease-in-out infinite both`,
              animationDelay: `${index * 0.16}s`,
              '@keyframes dotBounce': {
                '0%, 80%, 100%': {
                  transform: 'scale(0)',
                  opacity: 0.5,
                },
                '40%': {
                  transform: 'scale(1)',
                  opacity: 1,
                },
              },
            }}
          />
        ))}
      </Box>

      {/* Status Text */}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{
          textAlign: 'center',
          position: 'relative',
          zIndex: 2,
          opacity: 0.8,
        }}
      >
        This may take a few seconds...
      </Typography>

      {/* Floating Particles */}
      {[...Array(6)].map((_, index) => (
        <Box
          key={index}
          sx={{
            position: 'absolute',
            width: 4,
            height: 4,
            borderRadius: '50%',
            backgroundColor: 'primary.main',
            opacity: 0.3,
            animation: `floatParticle${index} ${3 + index * 0.5}s ease-in-out infinite`,
            [`@keyframes floatParticle${index}`]: {
              '0%': {
                transform: `translate(${Math.random() * 100 - 50}px, 100px) scale(0)`,
                opacity: 0,
              },
              '50%': {
                opacity: 0.6,
                transform: `translate(${Math.random() * 200 - 100}px, ${Math.random() * 50 - 25}px) scale(1)`,
              },
              '100%': {
                transform: `translate(${Math.random() * 100 - 50}px, -100px) scale(0)`,
                opacity: 0,
              },
            },
          }}
        />
      ))}
    </Box>
  );
};

export default LoadingAnimation;