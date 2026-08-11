import { useCallback, useEffect, useState } from 'react'

export function useReservationTimer(initialSeconds: number | null) {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(initialSeconds)

  useEffect(() => {
    setSecondsLeft(initialSeconds)
  }, [initialSeconds])

  useEffect(() => {
    if (secondsLeft == null || secondsLeft <= 0) return
    const t = setInterval(() => {
      setSecondsLeft((s) => (s != null && s > 0 ? s - 1 : 0))
    }, 1000)
    return () => clearInterval(t)
  }, [secondsLeft])

  const formatTime = useCallback(() => {
    if (secondsLeft == null) return '--:--'
    const m = Math.floor(secondsLeft / 60)
    const s = secondsLeft % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }, [secondsLeft])

  const expired = secondsLeft === 0

  return { secondsLeft, formatTime, expired, setSecondsLeft }
}
