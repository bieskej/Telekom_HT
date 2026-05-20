import { useEffect, useRef, useState } from 'react'

interface AnimatedNumberProps {
  value: number
  duration?: number
  decimals?: number
  suffix?: string
  className?: string
}

export function AnimatedNumber({
  value,
  duration = 800,
  decimals = 0,
  suffix = '',
  className,
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(value)
  const fromRef = useRef(value)

  useEffect(() => {
    const from = fromRef.current
    const target = value
    let start: number | null = null
    let frame: number

    const step = (ts: number) => {
      if (start == null) start = ts
      const t = Math.min(1, (ts - start) / duration)
      const eased = 1 - (1 - t) ** 3
      const next = from + (target - from) * eased
      setDisplay(next)
      if (t < 1) frame = requestAnimationFrame(step)
      else fromRef.current = target
    }

    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [value, duration])

  const formatted =
    decimals > 0
      ? display.toFixed(decimals)
      : Math.round(display).toLocaleString('hr-HR')

  return (
    <span className={className}>
      {formatted}
      {suffix}
    </span>
  )
}
