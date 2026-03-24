import { afterEach, describe, expect, it, vi } from 'vitest';

import { clearClientAuthState, guestUserSignIn } from './index';

describe('guestUserSignIn', () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('posts to the guest auth endpoint with cookies enabled', async () => {
		const payload = { token: 'guest-token', role: 'user', guest: true };
		const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
			ok: true,
			json: async () => payload
		} as Response);

		await expect(guestUserSignIn()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledWith(
			expect.stringMatching(/\/auths\/guest$/),
			expect.objectContaining({
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' }
			})
		);
	});

	it('throws the backend detail when guest auth is rejected', async () => {
		vi.spyOn(globalThis, 'fetch').mockResolvedValue({
			ok: false,
			json: async () => ({ detail: 'Access prohibited' })
		} as Response);

		await expect(guestUserSignIn()).rejects.toBe('Access prohibited');
	});
});

describe('clearClientAuthState', () => {
	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it('clears the persisted token and expires the auth cookie', () => {
		const removeItem = vi.fn();
		const localStorageMock = {
			removeItem
		};

		let cookieValue = 'token=guest-token';
		const documentMock = {} as { cookie: string };
		Object.defineProperty(documentMock, 'cookie', {
			get: () => cookieValue,
			set: (value: string) => {
				cookieValue = value;
			}
		});

		vi.stubGlobal('localStorage', localStorageMock);
		vi.stubGlobal('document', documentMock);

		clearClientAuthState();

		expect(removeItem).toHaveBeenCalledWith('token');
		expect(cookieValue).toBe('token=; Max-Age=0; path=/');
	});
});
