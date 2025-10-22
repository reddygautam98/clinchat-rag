import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline, Box } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { mobileTheme } from './theme/mobileTheme'
import { AuthProvider } from './contexts/AuthContext'
import { OfflineProvider } from './contexts/OfflineContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { LoadingScreen } from './components/common/LoadingScreen'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { BottomNavigation } from './components/navigation/BottomNavigation'
import { TopAppBar } from './components/navigation/TopAppBar'

// Lazy load components for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const PatientSearch = lazy(() => import('./pages/PatientSearch'))
const PatientDetails = lazy(() => import('./pages/PatientDetails'))
const DocumentViewer = lazy(() => import('./pages/DocumentViewer'))
const ChatInterface = lazy(() => import('./pages/ChatInterface'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))

// Create query client with mobile-optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes
      retry: (failureCount, error) => {
        // Don't retry on 401/403 errors
        if (error && 'status' in error && [401, 403].includes(error.status as number)) {
          return false
        }
        return failureCount < 2
      },
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: 1,
    },
  },
})

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={mobileTheme}>
          <CssBaseline />
          <AuthProvider>
            <OfflineProvider>
              <NotificationProvider>
                <Router>
                  <Box 
                    sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      minHeight: '100vh',
                      maxWidth: '100vw',
                      overflow: 'hidden'
                    }}
                  >
                    <TopAppBar />
                    
                    <Box 
                      component="main" 
                      sx={{ 
                        flex: 1, 
                        overflow: 'auto',
                        pb: 7, // Space for bottom navigation
                        px: { xs: 1, sm: 2 },
                        py: 1
                      }}
                    >
                      <Suspense fallback={<LoadingScreen />}>
                        <Routes>
                          <Route path="/login" element={<Login />} />
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/patients" element={<PatientSearch />} />
                          <Route path="/patients/:id" element={<PatientDetails />} />
                          <Route path="/documents/:id" element={<DocumentViewer />} />
                          <Route path="/chat" element={<ChatInterface />} />
                          <Route path="/settings" element={<Settings />} />
                        </Routes>
                      </Suspense>
                    </Box>
                    
                    <BottomNavigation />
                  </Box>
                </Router>
              </NotificationProvider>
            </OfflineProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App