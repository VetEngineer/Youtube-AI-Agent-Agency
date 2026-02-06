'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useApiKeys, useCreateApiKey, useDeleteApiKey } from '@/hooks/use-api-keys';
import { useChannels, useCreateChannel, useUpdateChannel, useDeleteChannel } from '@/hooks/use-channels';
import { Key, Plus, Trash2, Copy, Check, AlertCircle, Loader2, Settings2 } from 'lucide-react';

function ApiKeySection() {
    const { data, isLoading, error } = useApiKeys();
    const createApiKey = useCreateApiKey();
    const deleteApiKey = useDeleteApiKey();

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null);
    const [newKeyData, setNewKeyData] = useState({ name: '', scopes: ['read'], expires_days: 90 });
    const [createdKey, setCreatedKey] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const handleCreate = async () => {
        try {
            const result = await createApiKey.mutateAsync({
                name: newKeyData.name,
                scopes: newKeyData.scopes,
                expires_days: newKeyData.expires_days,
            });
            setCreatedKey(result.key);
            setNewKeyData({ name: '', scopes: ['read'], expires_days: 90 });
        } catch (err) {
            console.error('Failed to create API key:', err);
        }
    };

    const handleCopy = async () => {
        if (createdKey) {
            await navigator.clipboard.writeText(createdKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleDelete = async () => {
        if (deleteKeyId) {
            try {
                await deleteApiKey.mutateAsync(deleteKeyId);
                setDeleteKeyId(null);
            } catch (err) {
                console.error('Failed to delete API key:', err);
            }
        }
    };

    if (error) {
        const isAuthError = error instanceof Error && (error.message.includes('401') || error.message.includes('403'));
        return (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                <AlertCircle className="h-4 w-4 text-red-400" />
                <span className="text-sm text-red-400">
                    {isAuthError
                        ? 'Admin access required. Please use an API key with admin scope.'
                        : 'Failed to load API keys.'}
                </span>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-medium">API Keys</h4>
                    <p className="text-sm text-muted-foreground">Manage access keys for the API.</p>
                </div>
                <Dialog open={isCreateOpen} onOpenChange={(open) => {
                    setIsCreateOpen(open);
                    if (!open) {
                        setCreatedKey(null);
                        setCopied(false);
                    }
                }}>
                    <DialogTrigger asChild>
                        <Button size="sm">
                            <Plus className="h-4 w-4 mr-2" />
                            New Key
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{createdKey ? 'API Key Created' : 'Create API Key'}</DialogTitle>
                            <DialogDescription>
                                {createdKey
                                    ? 'Copy your new API key now. You will not be able to see it again.'
                                    : 'Create a new API key for accessing the API.'}
                            </DialogDescription>
                        </DialogHeader>
                        {createdKey ? (
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 p-3 bg-muted rounded-lg font-mono text-sm">
                                    <code className="flex-1 truncate">{createdKey}</code>
                                    <Button variant="ghost" size="icon" onClick={handleCopy}>
                                        {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                                    </Button>
                                </div>
                                <DialogFooter>
                                    <Button onClick={() => {
                                        setIsCreateOpen(false);
                                        setCreatedKey(null);
                                    }}>Done</Button>
                                </DialogFooter>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="key-name">Name</Label>
                                    <Input
                                        id="key-name"
                                        placeholder="My API Key"
                                        value={newKeyData.name}
                                        onChange={(e) => setNewKeyData({ ...newKeyData, name: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Scopes</Label>
                                    <Select
                                        value={newKeyData.scopes.includes('admin') ? 'admin' : 'read'}
                                        onValueChange={(val) => setNewKeyData({
                                            ...newKeyData,
                                            scopes: val === 'admin' ? ['admin', 'read', 'write'] : ['read']
                                        })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="read">Read Only</SelectItem>
                                            <SelectItem value="admin">Admin (Full Access)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="expires">Expires In (Days)</Label>
                                    <Input
                                        id="expires"
                                        type="number"
                                        value={newKeyData.expires_days}
                                        onChange={(e) => setNewKeyData({ ...newKeyData, expires_days: parseInt(e.target.value) || 90 })}
                                    />
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                                    <Button onClick={handleCreate} disabled={!newKeyData.name || createApiKey.isPending}>
                                        {createApiKey.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                        Create
                                    </Button>
                                </DialogFooter>
                            </div>
                        )}
                    </DialogContent>
                </Dialog>
            </div>

            <div className="border rounded-lg">
                {isLoading ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
                        Loading...
                    </div>
                ) : data?.api_keys && data.api_keys.length > 0 ? (
                    <div className="divide-y">
                        {data.api_keys.map((key) => (
                            <div key={key.key_id} className="p-4 flex items-center justify-between">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <Key className="h-4 w-4 text-muted-foreground" />
                                        <span className="font-medium">{key.name}</span>
                                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{key.prefix}...</code>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                                        {key.expires_at && (
                                            <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                                        )}
                                    </div>
                                    <div className="flex gap-1">
                                        {key.scopes.map((scope) => (
                                            <Badge key={scope} variant="secondary" className="text-xs">{scope}</Badge>
                                        ))}
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-red-400 hover:text-red-500 hover:bg-red-500/10"
                                    onClick={() => setDeleteKeyId(key.key_id)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        No API keys found. Create one to get started.
                    </div>
                )}
            </div>

            <AlertDialog open={!!deleteKeyId} onOpenChange={(open) => !open && setDeleteKeyId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. Applications using this key will no longer be able to access the API.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-red-500 hover:bg-red-600"
                        >
                            {deleteApiKey.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

function ChannelSection() {
    const { data, isLoading, error } = useChannels();
    const createChannel = useCreateChannel();
    const updateChannel = useUpdateChannel();
    const deleteChannel = useDeleteChannel();

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [editChannel, setEditChannel] = useState<{ channel_id: string; name: string; category: string } | null>(null);
    const [deleteChannelId, setDeleteChannelId] = useState<string | null>(null);
    const [newChannel, setNewChannel] = useState({ channel_id: '', name: '', category: 'general' });
    const [formError, setFormError] = useState<string | null>(null);

    const validateChannelId = (id: string) => /^[a-z0-9-]+$/.test(id);

    const handleCreate = async () => {
        setFormError(null);
        if (!validateChannelId(newChannel.channel_id)) {
            setFormError('Channel ID must contain only lowercase letters, numbers, and hyphens.');
            return;
        }
        try {
            await createChannel.mutateAsync(newChannel);
            setIsCreateOpen(false);
            setNewChannel({ channel_id: '', name: '', category: 'general' });
        } catch (err) {
            if (err instanceof Error && err.message.includes('409')) {
                setFormError('A channel with this ID already exists.');
            } else {
                setFormError('Failed to create channel.');
            }
        }
    };

    const handleUpdate = async () => {
        if (!editChannel) return;
        try {
            await updateChannel.mutateAsync({
                channelId: editChannel.channel_id,
                data: { name: editChannel.name, category: editChannel.category },
            });
            setEditChannel(null);
        } catch (err) {
            console.error('Failed to update channel:', err);
        }
    };

    const handleDelete = async () => {
        if (!deleteChannelId) return;
        try {
            await deleteChannel.mutateAsync(deleteChannelId);
            setDeleteChannelId(null);
        } catch (err) {
            console.error('Failed to delete channel:', err);
        }
    };

    if (error) {
        return (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                <AlertCircle className="h-4 w-4 text-red-400" />
                <span className="text-sm text-red-400">Failed to load channels.</span>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-medium">Channels</h4>
                    <p className="text-sm text-muted-foreground">Manage YouTube channel configurations.</p>
                </div>
                <Dialog open={isCreateOpen} onOpenChange={(open) => {
                    setIsCreateOpen(open);
                    if (!open) {
                        setFormError(null);
                        setNewChannel({ channel_id: '', name: '', category: 'general' });
                    }
                }}>
                    <DialogTrigger asChild>
                        <Button size="sm">
                            <Plus className="h-4 w-4 mr-2" />
                            New Channel
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Create Channel</DialogTitle>
                            <DialogDescription>Add a new channel configuration.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            {formError && (
                                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                    <AlertCircle className="h-4 w-4 text-red-400" />
                                    <span className="text-sm text-red-400">{formError}</span>
                                </div>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="channel-id">Channel ID</Label>
                                <Input
                                    id="channel-id"
                                    placeholder="my-tech-channel"
                                    value={newChannel.channel_id}
                                    onChange={(e) => setNewChannel({ ...newChannel, channel_id: e.target.value.toLowerCase() })}
                                />
                                <p className="text-xs text-muted-foreground">Lowercase letters, numbers, and hyphens only.</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="channel-name">Display Name</Label>
                                <Input
                                    id="channel-name"
                                    placeholder="My Tech Channel"
                                    value={newChannel.name}
                                    onChange={(e) => setNewChannel({ ...newChannel, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Category</Label>
                                <Select
                                    value={newChannel.category}
                                    onValueChange={(val) => setNewChannel({ ...newChannel, category: val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="general">General</SelectItem>
                                        <SelectItem value="technology">Technology</SelectItem>
                                        <SelectItem value="education">Education</SelectItem>
                                        <SelectItem value="entertainment">Entertainment</SelectItem>
                                        <SelectItem value="business">Business</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                                <Button
                                    onClick={handleCreate}
                                    disabled={!newChannel.channel_id || !newChannel.name || createChannel.isPending}
                                >
                                    {createChannel.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                    Create
                                </Button>
                            </DialogFooter>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="border rounded-lg">
                {isLoading ? (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
                        Loading...
                    </div>
                ) : data?.channels && data.channels.length > 0 ? (
                    <div className="divide-y">
                        {data.channels.map((channel) => (
                            <div key={channel.channel_id} className="p-4 flex items-center justify-between">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">{channel.name}</span>
                                        <Badge variant="secondary" className="text-xs">{channel.category}</Badge>
                                    </div>
                                    <code className="text-xs text-muted-foreground">{channel.channel_id}</code>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setEditChannel({
                                            channel_id: channel.channel_id,
                                            name: channel.name,
                                            category: channel.category,
                                        })}
                                    >
                                        <Settings2 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="text-red-400 hover:text-red-500 hover:bg-red-500/10"
                                        onClick={() => setDeleteChannelId(channel.channel_id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                        No channels found. Create one to get started.
                    </div>
                )}
            </div>

            <Dialog open={!!editChannel} onOpenChange={(open) => !open && setEditChannel(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Edit Channel</DialogTitle>
                        <DialogDescription>Update channel configuration.</DialogDescription>
                    </DialogHeader>
                    {editChannel && (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label>Channel ID</Label>
                                <Input value={editChannel.channel_id} disabled />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="edit-name">Display Name</Label>
                                <Input
                                    id="edit-name"
                                    value={editChannel.name}
                                    onChange={(e) => setEditChannel({ ...editChannel, name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Category</Label>
                                <Select
                                    value={editChannel.category}
                                    onValueChange={(val) => setEditChannel({ ...editChannel, category: val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="general">General</SelectItem>
                                        <SelectItem value="technology">Technology</SelectItem>
                                        <SelectItem value="education">Education</SelectItem>
                                        <SelectItem value="entertainment">Entertainment</SelectItem>
                                        <SelectItem value="business">Business</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setEditChannel(null)}>Cancel</Button>
                                <Button onClick={handleUpdate} disabled={updateChannel.isPending}>
                                    {updateChannel.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                    Save
                                </Button>
                            </DialogFooter>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            <AlertDialog open={!!deleteChannelId} onOpenChange={(open) => !open && setDeleteChannelId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Channel?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. All configurations for this channel will be permanently deleted.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-red-500 hover:bg-red-600"
                        >
                            {deleteChannel.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

function AuthSection() {
    const [apiKey, setApiKey] = useState('');
    const [savedKey, setSavedKey] = useState<string | null>(null);
    const [isSaved, setIsSaved] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem('api_key');
        if (stored) {
            setSavedKey(stored.substring(0, 10) + '...');
        }
    }, []);

    const handleSave = () => {
        if (apiKey) {
            localStorage.setItem('api_key', apiKey);
            setSavedKey(apiKey.substring(0, 10) + '...');
            setApiKey('');
            setIsSaved(true);
            setTimeout(() => setIsSaved(false), 2000);
        }
    };

    const handleClear = () => {
        localStorage.removeItem('api_key');
        setSavedKey(null);
    };

    return (
        <div className="space-y-4">
            <div>
                <h4 className="text-sm font-medium">Authentication</h4>
                <p className="text-sm text-muted-foreground">Configure your API key for accessing protected endpoints.</p>
            </div>

            <div className="border rounded-lg p-4 space-y-4">
                {savedKey && (
                    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                        <div className="flex items-center gap-2">
                            <Key className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">Current key: <code className="bg-muted px-1.5 py-0.5 rounded">{savedKey}</code></span>
                        </div>
                        <Button variant="ghost" size="sm" onClick={handleClear}>
                            Clear
                        </Button>
                    </div>
                )}

                <div className="flex gap-2">
                    <Input
                        type="password"
                        placeholder="Enter your API key"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                    />
                    <Button onClick={handleSave} disabled={!apiKey}>
                        {isSaved ? <Check className="h-4 w-4 mr-2" /> : null}
                        {isSaved ? 'Saved!' : 'Save'}
                    </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                    Your API key is stored locally and used for all API requests.
                </p>
            </div>
        </div>
    );
}

export default function SettingsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-medium">Settings</h3>
                <p className="text-sm text-muted-foreground">
                    Manage your API keys, channels, and authentication.
                </p>
            </div>

            <Tabs defaultValue="auth" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="auth">Authentication</TabsTrigger>
                    <TabsTrigger value="api-keys">API Keys</TabsTrigger>
                    <TabsTrigger value="channels">Channels</TabsTrigger>
                </TabsList>

                <TabsContent value="auth" className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <AuthSection />
                </TabsContent>

                <TabsContent value="api-keys" className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <ApiKeySection />
                </TabsContent>

                <TabsContent value="channels" className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <ChannelSection />
                </TabsContent>
            </Tabs>
        </div>
    );
}
