import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Chip,
  Container,
} from '@mui/material';
import { Analytics, TrendingUp } from '@mui/icons-material';

export const Header: React.FC = () => {
  return (
    <AppBar 
      position="static" 
      sx={{ 
        mb: 2,
        background: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
        animation: 'slideDown 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        '@keyframes slideDown': {
          '0%': {
            opacity: 0,
            transform: 'translateY(-20px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0px)',
          },
        },
      }}
    >
      <Container maxWidth="xl">
        <Toolbar sx={{ py: 0.5, minHeight: '56px !important' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 40,
                height: 40,
                borderRadius: 2,
                background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                boxShadow: '0 4px 12px rgba(63, 81, 181, 0.4)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'rotate(360deg) scale(1.1)',
                  boxShadow: '0 6px 20px rgba(63, 81, 181, 0.6)',
                },
              }}
            >
              <Analytics sx={{ fontSize: 24, color: 'white' }} />
            </Box>
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                fontWeight: 700,
                background: 'linear-gradient(45deg, #3f51b5, #f50057)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Outscaled.GG
            </Typography>
            <Chip
              label="BETA"
              color="secondary"
              size="small"
              sx={{ 
                ml: 1,
                fontWeight: 600,
                background: 'linear-gradient(45deg, #f50057, #ff4081)',
                color: 'white',
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': {
                    boxShadow: '0 0 0 0 rgba(245, 0, 87, 0.7)',
                  },
                  '70%': {
                    boxShadow: '0 0 0 4px rgba(245, 0, 87, 0)',
                  },
                  '100%': {
                    boxShadow: '0 0 0 0 rgba(245, 0, 87, 0)',
                  },
                },
                '& .MuiChip-label': {
                  px: 1,
                },
              }}
            />
          </Box>
          
          <Box sx={{ flexGrow: 1 }} />
          
          <Box 
            sx={{ 
              display: { xs: 'none', md: 'flex' }, 
              alignItems: 'center', 
              gap: 1,
              px: 1.5,
              py: 0.5,
              borderRadius: 1,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                transform: 'scale(1.02)',
              },
            }}
          >
            <TrendingUp sx={{ 
              color: 'primary.main', 
              fontSize: 18,
              animation: 'bounce 1s infinite',
              '@keyframes bounce': {
                '0%, 20%, 50%, 80%, 100%': {
                  transform: 'translateY(0)',
                },
                '40%': {
                  transform: 'translateY(-4px)',
                },
                '60%': {
                  transform: 'translateY(-2px)',
                },
              },
            }} />
            <Typography 
              variant="caption" 
              sx={{ 
                fontWeight: 500,
                color: 'text.secondary',
              }}
            >
              AI-Powered Predictions
            </Typography>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}; 