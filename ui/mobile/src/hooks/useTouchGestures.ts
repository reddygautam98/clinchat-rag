import { useState, useEffect, useCallback } from 'react'

export interface TouchGesture {
  startX: number
  startY: number
  currentX: number
  currentY: number
  deltaX: number
  deltaY: number
  distance: number
  direction: 'left' | 'right' | 'up' | 'down' | null
  isSwipe: boolean
  isLongPress: boolean
  duration: number
}

export interface UseTouchGesturesOptions {
  swipeThreshold?: number
  longPressThreshold?: number
  preventScrollOnSwipe?: boolean
}

export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  options: UseTouchGesturesOptions = {}
) => {
  const {
    swipeThreshold = 50,
    longPressThreshold = 500,
    preventScrollOnSwipe = false,
  } = options

  const [gesture, setGesture] = useState<TouchGesture | null>(null)
  const [isTracking, setIsTracking] = useState(false)

  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0]
    if (!touch) return

    const startTime = Date.now()
    const startX = touch.clientX
    const startY = touch.clientY

    setIsTracking(true)
    setGesture({
      startX,
      startY,
      currentX: startX,
      currentY: startY,
      deltaX: 0,
      deltaY: 0,
      distance: 0,
      direction: null,
      isSwipe: false,
      isLongPress: false,
      duration: 0,
    })

    // Long press detection
    const longPressTimer = setTimeout(() => {
      setGesture(prev => prev ? {
        ...prev,
        isLongPress: true,
        duration: Date.now() - startTime,
      } : null)
    }, longPressThreshold)

    // Store timer for cleanup
    ;(e.target as any)._longPressTimer = longPressTimer
  }, [longPressThreshold])

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!isTracking) return

    const touch = e.touches[0]
    if (!touch) return

    const currentX = touch.clientX
    const currentY = touch.clientY

    setGesture(prev => {
      if (!prev) return null

      const deltaX = currentX - prev.startX
      const deltaY = currentY - prev.startY
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
      
      let direction: TouchGesture['direction'] = null
      if (Math.abs(deltaX) > Math.abs(deltaY)) {
        direction = deltaX > 0 ? 'right' : 'left'
      } else {
        direction = deltaY > 0 ? 'down' : 'up'
      }

      const isSwipe = distance > swipeThreshold

      // Prevent scroll if swipe detected and option is enabled
      if (isSwipe && preventScrollOnSwipe) {
        e.preventDefault()
      }

      return {
        ...prev,
        currentX,
        currentY,
        deltaX,
        deltaY,
        distance,
        direction,
        isSwipe,
      }
    })
  }, [isTracking, swipeThreshold, preventScrollOnSwipe])

  const handleTouchEnd = useCallback((e: TouchEvent) => {
    setIsTracking(false)

    // Clear long press timer
    const target = e.target as any
    if (target._longPressTimer) {
      clearTimeout(target._longPressTimer)
      delete target._longPressTimer
    }

    // Reset gesture after a short delay to allow handlers to process
    setTimeout(() => {
      setGesture(null)
    }, 100)
  }, [])

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    element.addEventListener('touchstart', handleTouchStart, { passive: false })
    element.addEventListener('touchmove', handleTouchMove, { passive: false })
    element.addEventListener('touchend', handleTouchEnd, { passive: true })
    element.addEventListener('touchcancel', handleTouchEnd, { passive: true })

    return () => {
      element.removeEventListener('touchstart', handleTouchStart)
      element.removeEventListener('touchmove', handleTouchMove)
      element.removeEventListener('touchend', handleTouchEnd)
      element.removeEventListener('touchcancel', handleTouchEnd)
    }
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd])

  const onSwipeLeft = useCallback((callback: () => void) => {
    if (gesture?.isSwipe && gesture.direction === 'left') {
      callback()
    }
  }, [gesture])

  const onSwipeRight = useCallback((callback: () => void) => {
    if (gesture?.isSwipe && gesture.direction === 'right') {
      callback()
    }
  }, [gesture])

  const onSwipeUp = useCallback((callback: () => void) => {
    if (gesture?.isSwipe && gesture.direction === 'up') {
      callback()
    }
  }, [gesture])

  const onSwipeDown = useCallback((callback: () => void) => {
    if (gesture?.isSwipe && gesture.direction === 'down') {
      callback()
    }
  }, [gesture])

  const onLongPress = useCallback((callback: () => void) => {
    if (gesture?.isLongPress) {
      callback()
    }
  }, [gesture])

  return {
    gesture,
    isTracking,
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onLongPress,
  }
}