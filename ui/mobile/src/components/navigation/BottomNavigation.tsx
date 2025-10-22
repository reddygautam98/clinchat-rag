import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  BottomNavigation as MuiBottomNavigation,
  BottomNavigationAction,
  Paper,
  Badge,
  useTheme,
} from '@mui/material'
import {
  Home as HomeIcon,
  People as PatientsIcon,
  Chat as ChatIcon,
  Description as DocumentsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import { useOffline } from '../../hooks/useOffline'

interface NavigationItem {
  label: string
  value: string
  icon: React.ReactElement
  path: string
  badge?: number
  disabled?: boolean
}

const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    value: 'dashboard',
    icon: <HomeIcon />,
    path: '/',
  },
  {
    label: 'Patients',
    value: 'patients',
    icon: <PatientsIcon />,
    path: '/patients',
  },
  {
    label: 'Chat',
    value: 'chat',
    icon: <ChatIcon />,
    path: '/chat',
    badge: 0, // Will be updated with unread messages
  },
  {
    label: 'Documents',
    value: 'documents',
    icon: <DocumentsIcon />,
    path: '/documents',
  },
  {
    label: 'Settings',
    value: 'settings',
    icon: <SettingsIcon />,
    path: '/settings',
  },
]

export const BottomNavigation: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const theme = useTheme()
  const { isOffline } = useOffline()
  
  const [value, setValue] = useState<string>('')
  const [unreadMessages, setUnreadMessages] = useState(0)

  // Update active navigation based on current route
  useEffect(() => {
    const currentPath = location.pathname
    const activeItem = navigationItems.find(item => {
      if (item.path === '/') {
        return currentPath === '/'
      }
      return currentPath.startsWith(item.path)
    })
    
    setValue(activeItem?.value || '')
  }, [location.pathname])

  // Mock: Update unread message count
  useEffect(() => {
    // This would typically come from a real-time service or context
    const interval = setInterval(() => {
      // Simulate receiving messages
      setUnreadMessages(prev => prev + Math.floor(Math.random() * 2))
    }, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const handleNavigationChange = (event: React.SyntheticEvent, newValue: string) => {
    const item = navigationItems.find(nav => nav.value === newValue)
    if (item && !item.disabled) {
      setValue(newValue)
      navigate(item.path)
      
      // Clear badge for chat when navigating to it
      if (newValue === 'chat') {
        setUnreadMessages(0)
      }
    }
  }

  const renderNavigationAction = (item: NavigationItem) => {
    let icon = item.icon

    // Add badge for chat with unread messages
    if (item.value === 'chat' && unreadMessages > 0) {
      icon = (
        <Badge 
          badgeContent={unreadMessages > 99 ? '99+' : unreadMessages} 
          color="error"
          sx={{
            '& .MuiBadge-badge': {
              fontSize: '0.6rem',
              height: '16px',
              minWidth: '16px',
            },
          }}
        >
          {item.icon}
        </Badge>
      )
    }

    // Disable certain features when offline
    const disabled = isOffline && (item.value === 'chat' || item.value === 'patients')

    return (
      <BottomNavigationAction
        key={item.value}
        label={item.label}
        value={item.value}
        icon={icon}
        disabled={disabled}
        sx={{
          color: disabled ? theme.palette.text.disabled : undefined,
          '&.Mui-selected': {
            color: theme.palette.primary.main,
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.6875rem',
            marginTop: '4px',
          },
        }}
      />
    )
  }

  return (
    <Paper
      sx={{ 
        position: 'fixed', 
        bottom: 0, 
        left: 0, 
        right: 0,
        zIndex: 1000,
        borderTop: `1px solid ${theme.palette.divider}`,
      }}
      elevation={8}
    >
      <MuiBottomNavigation
        value={value}
        onChange={handleNavigationChange}
        showLabels
        sx={{
          backgroundColor: theme.palette.background.paper,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            paddingTop: '8px',
            paddingBottom: '8px',
          },
        }}
      >
        {navigationItems.map(renderNavigationAction)}
      </MuiBottomNavigation>
      
      {/* Offline indicator */}
      {isOffline && (
        <Paper
          elevation={0}
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            backgroundColor: theme.palette.warning.main,
            color: theme.palette.warning.contrastText,
            padding: '2px 8px',
            textAlign: 'center',
            fontSize: '0.6875rem',
            fontWeight: 500,
            transform: 'translateY(-100%)',
          }}
        >
          Offline Mode - Limited functionality
        </Paper>
      )}
    </Paper>
  )
}