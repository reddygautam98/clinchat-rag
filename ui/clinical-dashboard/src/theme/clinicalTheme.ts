import { createTheme, Theme } from '@mui/material/styles';

// Clinical color palette
const clinicalColors = {
  primary: {
    main: '#2E7D98', // Medical blue
    light: '#5BA5C7',
    dark: '#1F5A73',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#4A90A4', // Complementary teal
    light: '#7BB3C7',
    dark: '#346B7E',
    contrastText: '#ffffff',
  },
  success: {
    main: '#2E7D32', // Medical green
    light: '#4CAF50',
    dark: '#1B5E20',
  },
  warning: {
    main: '#F57C00', // Alert orange
    light: '#FF9800',
    dark: '#E65100',
  },
  error: {
    main: '#C62828', // Critical red
    light: '#E53935',
    dark: '#B71C1C',
  },
  info: {
    main: '#0277BD', // Information blue
    light: '#03A9F4',
    dark: '#01579B',
  },
  background: {
    default: '#F8F9FA',
    paper: '#FFFFFF',
  },
  text: {
    primary: '#212529',
    secondary: '#495057',
    disabled: '#6C757D',
  },
  divider: '#DEE2E6',
};

// Custom component overrides for clinical interface
const componentOverrides = {
  MuiAppBar: {
    styleOverrides: {
      root: {
        backgroundColor: clinicalColors.primary.main,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        border: '1px solid #E9ECEF',
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: '6px',
        textTransform: 'none',
        fontWeight: 500,
      },
      containedPrimary: {
        backgroundColor: clinicalColors.primary.main,
        '&:hover': {
          backgroundColor: clinicalColors.primary.dark,
        },
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: '6px',
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: '16px',
      },
      colorPrimary: {
        backgroundColor: clinicalColors.primary.light,
        color: clinicalColors.primary.contrastText,
      },
      colorSecondary: {
        backgroundColor: clinicalColors.secondary.light,
        color: clinicalColors.secondary.contrastText,
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: '6px',
      },
      standardError: {
        backgroundColor: '#FDEBEE',
        border: `1px solid ${clinicalColors.error.light}`,
      },
      standardWarning: {
        backgroundColor: '#FFF3E0',
        border: `1px solid ${clinicalColors.warning.light}`,
      },
      standardSuccess: {
        backgroundColor: '#E8F5E8',
        border: `1px solid ${clinicalColors.success.light}`,
      },
      standardInfo: {
        backgroundColor: '#E3F2FD',
        border: `1px solid ${clinicalColors.info.light}`,
      },
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: {
        backgroundColor: '#F8F9FA',
        '& .MuiTableCell-head': {
          fontWeight: 600,
          color: clinicalColors.text.primary,
        },
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        backgroundColor: '#FFFFFF',
        borderRight: '1px solid #E9ECEF',
      },
    },
  },
};

// Typography settings
const typography = {
  fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  h1: {
    fontSize: '2.5rem',
    fontWeight: 600,
    lineHeight: 1.2,
    color: clinicalColors.text.primary,
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.3,
    color: clinicalColors.text.primary,
  },
  h3: {
    fontSize: '1.75rem',
    fontWeight: 600,
    lineHeight: 1.3,
    color: clinicalColors.text.primary,
  },
  h4: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: clinicalColors.text.primary,
  },
  h5: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: clinicalColors.text.primary,
  },
  h6: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: clinicalColors.text.primary,
  },
  subtitle1: {
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
    color: clinicalColors.text.primary,
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    color: clinicalColors.text.secondary,
  },
  body1: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.5,
    color: clinicalColors.text.primary,
  },
  body2: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: 1.5,
    color: clinicalColors.text.secondary,
  },
  caption: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.4,
    color: clinicalColors.text.secondary,
  },
  overline: {
    fontSize: '0.75rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '0.5px',
    textTransform: 'uppercase',
    color: clinicalColors.text.secondary,
  },
};

// Create the clinical theme
export const clinicalTheme: Theme = createTheme({
  palette: {
    ...clinicalColors,
    mode: 'light',
  },
  typography,
  components: componentOverrides,
  shape: {
    borderRadius: 6,
  },
  spacing: 8,
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
  zIndex: {
    appBar: 1200,
    drawer: 1100,
    modal: 1300,
    snackbar: 1400,
    tooltip: 1500,
  },
});

// Clinical-specific theme extensions
declare module '@mui/material/styles' {
  interface Theme {
    clinical: {
      severity: {
        critical: string;
        high: string;
        medium: string;
        low: string;
        info: string;
      };
      phi: {
        detected: string;
        safe: string;
      };
      analysis: {
        pending: string;
        inProgress: string;
        completed: string;
        failed: string;
      };
    };
  }
  
  interface ThemeOptions {
    clinical?: {
      severity?: {
        critical?: string;
        high?: string;
        medium?: string;
        low?: string;
        info?: string;
      };
      phi?: {
        detected?: string;
        safe?: string;
      };
      analysis?: {
        pending?: string;
        inProgress?: string;
        completed?: string;
        failed?: string;
      };
    };
  }
}

// Add clinical extensions to the theme
clinicalTheme.clinical = {
  severity: {
    critical: '#C62828',
    high: '#F57C00',
    medium: '#FBC02D',
    low: '#689F38',
    info: '#0277BD',
  },
  phi: {
    detected: '#C62828',
    safe: '#2E7D32',
  },
  analysis: {
    pending: '#757575',
    inProgress: '#0277BD',
    completed: '#2E7D32',
    failed: '#C62828',
  },
};

export default clinicalTheme;