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
        mb: 3,
        background: 'rgba(26, 26, 26, 0.8)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
      }}
    >
      <Container maxWidth="xl">
        <Toolbar sx={{ py: 1 }}>
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
              }}
            >
              <Analytics sx={{ fontSize: 24, color: 'white' }} />
            </Box>
            <Typography 
              variant="h4" 
              component="div" 
              sx={{ 
                fontWeight: 800,
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
                '& .MuiChip-label': {
                  px: 1,
                },
              }}
            />
          </Box>
          
          <Box sx={{ flexGrow: 1 }} />
          
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1,
              px: 2,
              py: 1,
              borderRadius: 2,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <TrendingUp sx={{ color: 'primary.main' }} />
            <Typography 
              variant="body2" 
              sx={{ 
                display: { xs: 'none', sm: 'block' },
                fontWeight: 500,
                color: 'text.secondary',
              }}
            >
              AI-Powered LoL Prop Predictions
            </Typography>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}; 