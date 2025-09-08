import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { SessionData, createSession, getSession, updateSession } from '../lib/api'
import { generateSessionToken } from '../lib/utils'

interface SessionContextType {
  session: SessionData | null
  loading: boolean
  error: string | null
  updateSessionData: (data: Partial<SessionData>) => Promise<void>
  refreshSession: () => Promise<void>
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

interface SessionProviderProps {
  children: ReactNode
}

export function SessionProvider({ children }: SessionProviderProps) {
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const initializeSession = async () => {
    try {
      setLoading(true)
      setError(null)

      // Check if we have a session token in localStorage
      let sessionToken = localStorage.getItem('session_token')
      
      if (sessionToken) {
        try {
          // Try to retrieve existing session
          const sessionData = await getSession(sessionToken)
          setSession(sessionData)
          return
        } catch (error) {
          // Session expired or invalid, create new one
          console.warn('Existing session invalid, creating new one')
          localStorage.removeItem('session_token')
        }
      }

      // Create new session
      const newSession = await createSession()
      localStorage.setItem('session_token', newSession.session_token)
      setSession(newSession)
      
    } catch (err) {
      console.error('Failed to initialize session:', err)
      setError('Failed to initialize session')
    } finally {
      setLoading(false)
    }
  }

  const updateSessionData = async (data: Partial<SessionData>) => {
    if (!session) return

    try {
      await updateSession(session.session_token, data)
      setSession(prev => prev ? { ...prev, ...data } : null)
    } catch (err) {
      console.error('Failed to update session:', err)
      setError('Failed to update session')
    }
  }

  const refreshSession = async () => {
    if (!session) return

    try {
      const updatedSession = await getSession(session.session_token)
      setSession(updatedSession)
    } catch (err) {
      console.error('Failed to refresh session:', err)
      setError('Failed to refresh session')
    }
  }

  useEffect(() => {
    initializeSession()
  }, [])

  const value: SessionContextType = {
    session,
    loading,
    error,
    updateSessionData,
    refreshSession,
  }

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return context
}
