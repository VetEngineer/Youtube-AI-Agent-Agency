'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error(error)
    }, [error])

    return (
        <div className="flex h-[50vh] w-full flex-col items-center justify-center gap-4">
            <div className="text-center">
                <h2 className="text-2xl font-bold text-balance">Something went wrong!</h2>
                <p className="text-muted-foreground">{error.message || "An unexpected error occurred."}</p>
            </div>
            <Button onClick={() => reset()}>
                Try again
            </Button>
        </div>
    )
}
