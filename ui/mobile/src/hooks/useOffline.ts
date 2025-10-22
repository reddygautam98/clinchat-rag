import { useState, useEffect } from 'react'

export interface OfflineState {
  isOffline: boolean
  lastOnline: Date | null
  connectionType: string | null
}

export const useOffline = () => {
  const [offlineState, setOfflineState] = useState<OfflineState>({
    isOffline: !navigator.onLine,
    lastOnline: navigator.onLine ? new Date() : null,
    connectionType: null,
  })

  useEffect(() => {
    const handleOnline = () => {
      setOfflineState(prev => ({
        ...prev,
        isOffline: false,
        lastOnline: new Date(),
        connectionType: getConnectionType(),
      }))
    }

    const handleOffline = () => {
      setOfflineState(prev => ({
        ...prev,
        isOffline: true,
        connectionType: null,
      }))
    }

    const handleConnectionChange = () => {
      setOfflineState(prev => ({
        ...prev,
        connectionType: getConnectionType(),
      }))
    }

    // Add event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    // Listen for connection changes (if supported)
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      connection?.addEventListener('change', handleConnectionChange)
    }

    // Initial connection type
    setOfflineState(prev => ({
      ...prev,
      connectionType: getConnectionType(),
    }))

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      
      if ('connection' in navigator) {
        const connection = (navigator as any).connection
        connection?.removeEventListener('change', handleConnectionChange)
      }
    }
  }, [])

  return {
    isOffline: offlineState.isOffline,
    isOnline: !offlineState.isOffline,
    lastOnline: offlineState.lastOnline,
    connectionType: offlineState.connectionType,
    connectionQuality: getConnectionQuality(offlineState.connectionType),
  }
}

const getConnectionType = (): string | null => {
  if ('connection' in navigator) {
    const connection = (navigator as any).connection
    return connection?.effectiveType || connection?.type || null
  }
  return null
}

const getConnectionQuality = (connectionType: string | null): 'good' | 'fair' | 'poor' | 'unknown' => {
  if (!connectionType) return 'unknown'
  
  switch (connectionType) {
    case '4g':
    case 'wifi':
      return 'good'
    case '3g':
      return 'fair'
    case '2g':
    case 'slow-2g':
      return 'poor'
    default:
      return 'unknown'
  }
}