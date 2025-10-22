import { createTheme, responsiveFontSizes } from '@mui/material/styles'
import { alpha } from '@mui/material/styles'

// Mobile-optimized theme for ClinChat-RAG
const baseMobileTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
      contrastText: '#ffffff',
    },
    error: {
      main: '#f44336',
      light: '#e57373',
      dark: '#d32f2f',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 14,
    // Mobile-optimized font sizes
    h1: {
      fontSize: '1.75rem',
      fontWeight: 500,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.125rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.75rem',
      lineHeight: 1.43,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      textTransform: 'none' as const,
    },
    caption: {
      fontSize: '0.6875rem',
      lineHeight: 1.5,
    },
  },
  spacing: 8,
  shape: {
    borderRadius: 8,
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
  components: {
    // Mobile-optimized component styles
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: '44px', // Touch-friendly minimum height
          paddingTop: '12px',
          paddingBottom: '12px',
          borderRadius: '8px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minWidth: '44px',
          minHeight: '44px',
          padding: '10px',
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          width: '56px',
          height: '56px',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            minHeight: '44px',
          },
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: {
          minHeight: '56px',
          paddingTop: '12px',
          paddingBottom: '12px',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          minHeight: '56px',
          paddingTop: '12px',
          paddingBottom: '12px',
          borderRadius: '8px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: '16px',
          '&:last-child': {
            paddingBottom: '16px',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
        },
      },
    },
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          height: '64px',
          boxShadow: '0 -1px 3px rgba(0,0,0,0.12)',
        },
      },
    },
    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          minWidth: 'auto',
          paddingTop: '8px',
          '&.Mui-selected': {
            paddingTop: '8px',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          height: '32px',
          fontSize: '0.75rem',
        },
        clickable: {
          '&:hover': {
            backgroundColor: alpha('#1976d2', 0.08),
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          width: '280px',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          margin: '16px',
          width: 'calc(100% - 32px)',
          maxWidth: '400px',
        },
      },
    },
    MuiSnackbar: {
      styleOverrides: {
        root: {
          bottom: '80px', // Above bottom navigation
        },
      },
    },
    // Data Grid mobile optimization
    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: 'none',
          '& .MuiDataGrid-cell': {
            fontSize: '0.75rem',
            padding: '8px',
          },
          '& .MuiDataGrid-columnHeader': {
            fontSize: '0.75rem',
            fontWeight: 600,
          },
        },
      },
    },
  },
  // Custom mixins for mobile
  mixins: {
    toolbar: {
      minHeight: '56px',
      '@media (min-width:0px) and (orientation: landscape)': {
        minHeight: '48px',
      },
      '@media (min-width:600px)': {
        minHeight: '64px',
      },
    },
  },
})

// Apply responsive font sizes
export const mobileTheme = responsiveFontSizes(baseMobileTheme, {
  factor: 2,
  variants: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'body1', 'body2'],
})

// Dark theme variant
export const mobileDarkTheme = responsiveFontSizes(createTheme({
  ...baseMobileTheme,
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
      light: '#e3f2fd',
      dark: '#42a5f5',
    },
    secondary: {
      main: '#f48fb1',
      light: '#fce4ec',
      dark: '#ad2d5f',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.5)',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
}), {
  factor: 2,
  variants: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'body1', 'body2'],
})

// Theme variants for different screen orientations
export const getOrientationTheme = (orientation: 'portrait' | 'landscape') => {
  return createTheme({
    ...mobileTheme,
    components: {
      ...mobileTheme.components,
      MuiAppBar: {
        styleOverrides: {
          root: {
            height: orientation === 'landscape' ? '48px' : '56px',
          },
        },
      },
      MuiBottomNavigation: {
        styleOverrides: {
          root: {
            height: orientation === 'landscape' ? '56px' : '64px',
          },
        },
      },
    },
  })
}