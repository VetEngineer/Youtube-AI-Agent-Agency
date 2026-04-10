import { load, type Store } from '@tauri-apps/plugin-store'

const STORE_PATH = 'yaa.json'

export const DEFAULT_BACKEND_URL = 'https://ytai.hakhamsolution.co.kr/api/v1'

// Cache the promise (not the resolved value) so concurrent callers share one load() call.
let _storePromise: Promise<Store> | null = null

function getStoreInstance(): Promise<Store> {
  if (!_storePromise) {
    _storePromise = load(STORE_PATH, { defaults: {}, autoSave: true }).catch((err: unknown) => {
      // Clear so the next call can retry rather than returning a permanently-rejected Promise.
      _storePromise = null
      throw err
    })
  }
  return _storePromise
}

export async function getApiKey(): Promise<string | null> {
  const store = await getStoreInstance()
  return (await store.get<string>('api_key')) ?? null
}

export async function setApiKey(key: string): Promise<void> {
  const store = await getStoreInstance()
  await store.set('api_key', key)
}

export async function clearApiKey(): Promise<void> {
  const store = await getStoreInstance()
  await store.delete('api_key')
}

export async function getBackendUrl(): Promise<string> {
  const store = await getStoreInstance()
  return (await store.get<string>('backend_url')) ?? DEFAULT_BACKEND_URL
}

export async function setBackendUrl(url: string): Promise<void> {
  const store = await getStoreInstance()
  await store.set('backend_url', url)
}

export async function getOutputDir(): Promise<string | null> {
  const store = await getStoreInstance()
  return (await store.get<string>('output_dir')) ?? null
}

export async function setOutputDir(dir: string): Promise<void> {
  const store = await getStoreInstance()
  await store.set('output_dir', dir)
}

/** Remote backend URL — only set during remote-server auth, never changed by local mode. */
export async function getRemoteBackendUrl(): Promise<string> {
  const store = await getStoreInstance()
  return (await store.get<string>('remote_backend_url')) ?? DEFAULT_BACKEND_URL
}

export async function setRemoteBackendUrl(url: string): Promise<void> {
  const store = await getStoreInstance()
  await store.set('remote_backend_url', url)
}

export async function hasOnboarded(): Promise<boolean> {
  const store = await getStoreInstance()
  return (await store.get<boolean>('has_onboarded')) === true
}

export async function setOnboarded(): Promise<void> {
  const store = await getStoreInstance()
  await store.set('has_onboarded', true)
}

export async function getBackendMode(): Promise<'remote' | 'local'> {
  const store = await getStoreInstance()
  const val = await store.get<string>('backend_mode')
  return val === 'local' ? 'local' : 'remote'
}

export async function setBackendMode(mode: 'remote' | 'local'): Promise<void> {
  const store = await getStoreInstance()
  await store.set('backend_mode', mode)
}

export async function getLocalBackendPort(): Promise<number> {
  const store = await getStoreInstance()
  const val = await store.get<number>('local_backend_port')
  return typeof val === 'number' && val > 0 ? val : 8000
}
