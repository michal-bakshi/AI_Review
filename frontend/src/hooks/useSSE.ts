/** Custom hook for consuming a Server-Sent Events stream. */

import { useEffect, useRef, useState } from 'react'
import { SSE_CONNECTION_ERROR, SSE_DONE, SSE_ERROR_PREFIX } from '../constants/sse'

interface UseSSEResult {
  chunks: string[]
  isStreaming: boolean
  error: string | null
}

export function useSSE(url: string | null): UseSSEResult {
  const [chunks, setChunks] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!url) return

    setChunks([])
    setIsStreaming(true)
    setError(null)

    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (e: MessageEvent) => {
      if (e.data === SSE_DONE) {
        setIsStreaming(false)
        es.close()
        return
      }
      if (e.data.startsWith(SSE_ERROR_PREFIX)) {
        setError(e.data)
        setIsStreaming(false)
        es.close()
        return
      }
      setChunks((prev) => [...prev, e.data])
    }

    es.onerror = () => {
      setError(SSE_CONNECTION_ERROR)
      setIsStreaming(false)
      es.close()
    }

    return () => {
      es.close()
    }
  }, [url])

  return { chunks, isStreaming, error }
}
