import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

interface ErrorBoundaryProps {
  children: ReactNode
  /** Kratki naziv ekrana za poruku (npr. "Brojevi"). */
  title?: string
}

interface ErrorBoundaryState {
  error: string | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(err: Error): ErrorBoundaryState {
    return { error: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    console.error(this.props.title ?? 'ErrorBoundary', err, info.componentStack)
  }

  private reset = () => {
    this.setState({ error: null })
  }

  render() {
    if (this.state.error) {
      const label = this.props.title ?? 'Stranica'
      return (
        <Card>
          <CardContent className="space-y-4 p-8 text-sm">
            <p className="font-medium text-red-600">
              Greška prikaza ({label}): {this.state.error}
            </p>
            <Button type="button" variant="outline" size="sm" onClick={this.reset}>
              Pokušaj ponovno
            </Button>
          </CardContent>
        </Card>
      )
    }
    return this.props.children
  }
}
