export default function SettingsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-medium">Settings</h3>
                <p className="text-sm text-muted-foreground">
                    Manage your API keys and channel configurations.
                </p>
            </div>
            <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <h4 className="text-sm font-medium">API Keys</h4>
                            <p className="text-sm text-muted-foreground">
                                Manage access keys for the Youtube Agent API.
                            </p>
                        </div>
                        {/* Action button placeholder */}
                    </div>
                    <div className="border-t pt-4">
                        <p className="text-sm text-muted-foreground">No API keys found.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
