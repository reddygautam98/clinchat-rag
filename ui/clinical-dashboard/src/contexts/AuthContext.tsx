import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { toast } from 'react-toastify';
import Cookies from 'js-cookie';
import { authAPI } from '../services/api/authAPI';

// Types
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  department?: string;
  licenseNumber?: string;
  specialties?: string[];
  isActive: boolean;
  lastLogin?: string;
  permissions: string[];
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  token: string | null;
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string, remember?: boolean) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  updateProfile: (updates: Partial<User>) => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

interface AuthProviderProps {
  children: ReactNode;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    loading: true,
    token: null,
  });

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  // Auto-refresh token
  useEffect(() => {
    if (state.isAuthenticated && state.token) {
      const interval = setInterval(() => {
        refreshToken();
      }, 15 * 60 * 1000); // Refresh every 15 minutes

      return () => clearInterval(interval);
    }
  }, [state.isAuthenticated, state.token]);

  const initializeAuth = async () => {
    try {
      const storedToken = Cookies.get('clinchat_token');
      
      if (storedToken) {
        // Validate token and get user info
        const userData = await authAPI.validateToken(storedToken);
        
        if (userData) {
          setState({
            user: userData,
            isAuthenticated: true,
            loading: false,
            token: storedToken,
          });
          
          // Set authorization header for future requests
          authAPI.setAuthHeader(storedToken);
        } else {
          // Invalid token, clear it
          Cookies.remove('clinchat_token');
          setState({
            user: null,
            isAuthenticated: false,
            loading: false,
            token: null,
          });
        }
      } else {
        setState(prev => ({
          ...prev,
          loading: false,
        }));
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      setState({
        user: null,
        isAuthenticated: false,
        loading: false,
        token: null,
      });
    }
  };

  const login = async (email: string, password: string, remember = false): Promise<boolean> => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      
      const response = await authAPI.login(email, password);
      
      if (response.success && response.user && response.token) {
        // Store token in cookies
        const cookieOptions = remember 
          ? { expires: 30, secure: true, sameSite: 'strict' as const }
          : { secure: true, sameSite: 'strict' as const };
        
        Cookies.set('clinchat_token', response.token, cookieOptions);
        
        // Update state
        setState({
          user: response.user,
          isAuthenticated: true,
          loading: false,
          token: response.token,
        });
        
        // Set authorization header
        authAPI.setAuthHeader(response.token);
        
        toast.success(`Welcome back, ${response.user.firstName}!`);
        
        // Log audit event
        await authAPI.logAuditEvent({
          eventType: 'user_login',
          userId: response.user.id,
          details: { email, loginMethod: 'password' },
        });
        
        return true;
      } else {
        toast.error(response.message || 'Login failed');
        setState(prev => ({ ...prev, loading: false }));
        return false;
      }
    } catch (error: any) {
      console.error('Login error:', error);
      toast.error(error.message || 'Login failed. Please try again.');
      setState(prev => ({ ...prev, loading: false }));
      return false;
    }
  };

  const logout = async () => {
    try {
      if (state.user) {
        // Log audit event
        await authAPI.logAuditEvent({
          eventType: 'user_logout',
          userId: state.user.id,
          details: { logoutMethod: 'manual' },
        });
      }
      
      // Call logout API
      if (state.token) {
        await authAPI.logout(state.token);
      }
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Clear local state regardless of API response
      Cookies.remove('clinchat_token');
      authAPI.clearAuthHeader();
      
      setState({
        user: null,
        isAuthenticated: false,
        loading: false,
        token: null,
      });
      
      toast.info('You have been logged out');
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const currentToken = state.token || Cookies.get('clinchat_token');
      
      if (!currentToken) return false;
      
      const response = await authAPI.refreshToken(currentToken);
      
      if (response.success && response.token) {
        // Update stored token
        Cookies.set('clinchat_token', response.token, { 
          secure: true, 
          sameSite: 'strict' 
        });
        
        // Update state
        setState(prev => ({
          ...prev,
          token: response.token,
        }));
        
        // Update auth header
        authAPI.setAuthHeader(response.token);
        
        return true;
      } else {
        // Refresh failed, logout user
        logout();
        return false;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
      return false;
    }
  };

  const updateProfile = async (updates: Partial<User>): Promise<boolean> => {
    try {
      if (!state.user) return false;
      
      const response = await authAPI.updateProfile(state.user.id, updates);
      
      if (response.success && response.user) {
        setState(prev => ({
          ...prev,
          user: response.user,
        }));
        
        toast.success('Profile updated successfully');
        return true;
      } else {
        toast.error(response.message || 'Failed to update profile');
        return false;
      }
    } catch (error: any) {
      console.error('Profile update error:', error);
      toast.error(error.message || 'Failed to update profile');
      return false;
    }
  };

  const hasPermission = (permission: string): boolean => {
    return state.user?.permissions?.includes(permission) || false;
  };

  const hasRole = (role: string): boolean => {
    return state.user?.roles?.includes(role) || false;
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    updateProfile,
    hasPermission,
    hasRole,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext;