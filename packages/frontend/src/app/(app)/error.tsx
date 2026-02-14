'use client'

import { useEffect } from 'react'

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
                <h2 className="text-2xl font-bold">Something went wrong!</h2>
                <p className="text-muted-foreground">{error.message || "An unexpected error occurred."}</p>
            </div>
            <button
                onClick={() => reset()}
                className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
            >
                Try again
            </button>
        </div>
    )
}
