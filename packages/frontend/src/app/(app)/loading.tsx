export default function Loading() {
    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <div className="h-9 w-40 rounded bg-muted/20 animate-pulse motion-reduce:animate-none" />
                <div className="h-10 w-36 rounded bg-muted/20 animate-pulse motion-reduce:animate-none" />
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-32 rounded-xl bg-muted/20 animate-pulse motion-reduce:animate-none" />
                ))}
            </div>
        </div>
    )
}
