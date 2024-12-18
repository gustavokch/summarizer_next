'use client'

import { Toaster } from 'sonner'

export function ToastProvider() {
  return (
    <Toaster 
      position="top-right" 
      richColors 
      expand={false}
      pauseWhenPageIsHidden
    />
  )
}