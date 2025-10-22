import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Badge,
  Box,
  useTheme,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
} from '@mui/icons-material'
import { useAuth } from '../../hooks/useAuth'
import { useNotifications } from '../../hooks/useNotifications'
import { useThemeMode } from '../../hooks/useThemeMode'
import { useOffline } from '../../hooks/useOffline'

const pageNames: Record<string, string> = {
  '/': 'Dashboard',
  '/patients': 'Patients',
  '/chat': 'AI Assistant',
  '/documents': 'Documents', 
  '/settings': 'Settings',
}

export const TopAppBar: React.FC = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const theme = useTheme()
  const { user, logout } = useAuth()
  const { notifications, markAsRead } = useNotifications()
  const { isDark, toggleTheme } = useThemeMode()
  const { isOffline } = useOffline()

  const [menuOpen, setMenuOpen] = useState(false)
  const [accountMenuAnchor, setAccountMenuAnchor] = useState<null | HTMLElement>(null)
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<null | HTMLElement>(null)

  const currentPageName = pageNames[location.pathname] || 'ClinChat-RAG'
  const unreadNotifications = notifications.filter(n => !n.read).length

  const handleMenuOpen = () => {
    setMenuOpen(true)
  }

  const handleMenuClose = () => {
    setMenuOpen(false)
  }

  const handleAccountMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAccountMenuAnchor(event.currentTarget)
  }

  const handleAccountMenuClose = () => {
    setAccountMenuAnchor(null)
  }

  const handleNotificationMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationMenuAnchor(event.currentTarget)
  }

  const handleNotificationMenuClose = () => {
    setNotificationMenuAnchor(null)
  }

  const handleLogout = async () => {
    await logout()
    handleAccountMenuClose()
    navigate('/login')
  }

  const handleNotificationClick = (notificationId: string) => {
    markAsRead(notificationId)
    handleNotificationMenuClose()
    // Navigate to relevant page based on notification type
  }

  const menuItems = [
    { 
      text: 'Dashboard', 
      icon: <MenuIcon />, 
      path: '/' 
    },
    { 
      text: 'Patients', 
      icon: <PersonIcon />, 
      path: '/patients',
      disabled: isOffline 
    },
    { 
      text: 'AI Assistant', 
      icon: <SearchIcon />, 
      path: '/chat',
      disabled: isOffline
    },
    { 
      text: 'Documents', 
      icon: <MenuIcon />, 
      path: '/documents' 
    },
    { 
      text: 'Settings', 
      icon: <SettingsIcon />, 
      path: '/settings' 
    },
  ]

  return (
    <>
      <AppBar 
        position="fixed" 
        color="primary"
        elevation={1}
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          backgroundColor: isOffline ? theme.palette.warning.main : undefined,
        }}
      >
        <Toolbar 
          variant="dense"
          sx={{ 
            minHeight: { xs: '56px', sm: '64px' },
            paddingX: { xs: 1, sm: 2 },
          }}
        >
          {/* Menu Button */}
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={handleMenuOpen}
            sx={{ mr: 1 }}
          >
            <MenuIcon />
          </IconButton>

          {/* Page Title */}
          <Typography 
            variant="h6" 
            component="h1"
            sx={{ 
              flexGrow: 1,
              fontSize: { xs: '1rem', sm: '1.25rem' },
              fontWeight: 500,
            }}
          >
            {isOffline ? 'Offline - ' : ''}{currentPageName}
          </Typography>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            
            {/* Search Button (mobile) */}
            <IconButton
              color="inherit"
              aria-label="search"
              onClick={() => navigate('/search')}
              sx={{ display: { xs: 'flex', sm: 'none' } }}
            >
              <SearchIcon />
            </IconButton>

            {/* Notifications */}
            <IconButton
              color="inherit"
              aria-label="notifications"
              onClick={handleNotificationMenuOpen}
              disabled={isOffline}
            >
              <Badge badgeContent={unreadNotifications} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>

            {/* Theme Toggle */}
            <IconButton
              color="inherit"
              aria-label="toggle theme"
              onClick={toggleTheme}
            >
              {isDark ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>

            {/* Account Menu */}
            <IconButton
              color="inherit"
              aria-label="account"
              onClick={handleAccountMenuOpen}
            >
              {user?.avatar ? (
                <Avatar 
                  src={user.avatar} 
                  sx={{ width: 32, height: 32 }}
                />
              ) : (
                <AccountIcon />
              )}
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        anchor="left"
        open={menuOpen}
        onClose={handleMenuClose}
        sx={{
          '& .MuiDrawer-paper': {
            width: 280,
            paddingTop: { xs: '56px', sm: '64px' },
          },
        }}
      >
        <Box sx={{ px: 2, py: 2 }}>
          <Typography variant="h6" color="primary" gutterBottom>
            ClinChat-RAG
          </Typography>
          <Typography variant="body2" color="text.secondary">
            AI-Powered Clinical Assistant
          </Typography>
        </Box>
        
        <Divider />
        
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                onClick={() => {
                  navigate(item.path)
                  handleMenuClose()
                }}
                disabled={item.disabled}
                selected={location.pathname === item.path}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  mb: 0.5,
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Account Menu */}
      <Menu
        anchorEl={accountMenuAnchor}
        open={Boolean(accountMenuAnchor)}
        onClose={handleAccountMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => { navigate('/profile'); handleAccountMenuClose(); }}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>
          Profile
        </MenuItem>
        
        <MenuItem onClick={() => { navigate('/settings'); handleAccountMenuClose(); }}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          Settings
        </MenuItem>
        
        <MenuItem onClick={() => { navigate('/help'); handleAccountMenuClose(); }}>
          <ListItemIcon>
            <HelpIcon fontSize="small" />
          </ListItemIcon>
          Help
        </MenuItem>
        
        <Divider />
        
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>

      {/* Notifications Menu */}
      <Menu
        anchorEl={notificationMenuAnchor}
        open={Boolean(notificationMenuAnchor)}
        onClose={handleNotificationMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          sx: { width: 320, maxHeight: 400 }
        }}
      >
        {notifications.length === 0 ? (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              No notifications
            </Typography>
          </MenuItem>
        ) : (
          notifications.slice(0, 5).map((notification) => (
            <MenuItem 
              key={notification.id}
              onClick={() => handleNotificationClick(notification.id)}
              sx={{
                backgroundColor: notification.read ? 'transparent' : theme.palette.action.hover,
                whiteSpace: 'normal',
                maxWidth: 320,
              }}
            >
              <Box>
                <Typography variant="body2" fontWeight={notification.read ? 'normal' : 'bold'}>
                  {notification.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {notification.message}
                </Typography>
              </Box>
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  )
}