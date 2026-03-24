import { describe, expect, it } from 'vitest';

type GuestBootstrapInputs = {
	search: string;
	enableGuestAccess: boolean;
	hasResolvedUser: boolean;
};

type AutomaticSignInInputs = {
	guestSignInSucceeded: boolean;
	authTrustedHeader: boolean;
	authEnabled: boolean;
};

type RootLayoutBootstrapInputs = {
	token: string | null;
	sessionUser: { id: string } | null;
	currentPath: string;
	currentSearch: string;
};

const shouldAttemptGuestBootstrap = ({
	search,
	enableGuestAccess,
	hasResolvedUser
}: GuestBootstrapInputs) => {
	const params = new URLSearchParams(search);
	return params.get('guest') === '1' && enableGuestAccess && !hasResolvedUser;
};

const shouldRunAutomaticSignIn = ({
	guestSignInSucceeded,
	authTrustedHeader,
	authEnabled
}: AutomaticSignInInputs) => {
	if (guestSignInSucceeded) {
		return false;
	}

	return authTrustedHeader || authEnabled === false;
};

const resolveRootLayoutBootstrap = ({
	token,
	sessionUser,
	currentPath,
	currentSearch
}: RootLayoutBootstrapInputs) => {
	const encodedUrl = encodeURIComponent(`${currentPath}${currentSearch}`);

	if (!token) {
		if (currentPath === '/auth') {
			return { action: 'stay-on-auth' as const };
		}

		return { action: 'redirect-to-auth' as const, target: `/auth?redirect=${encodedUrl}` };
	}

	if (sessionUser) {
		return {
			action: 'restore-session' as const,
			socketAuthTokenSource: token
		};
	}

	return {
		action: 'clear-and-redirect' as const,
		target: `/auth?redirect=${encodedUrl}`
	};
};

describe('guest auth entry flow helpers', () => {
	it('attempts guest bootstrap only for guest routes with feature enabled and no active session', () => {
		expect(
			shouldAttemptGuestBootstrap({
				search: '?guest=1',
				enableGuestAccess: true,
				hasResolvedUser: false
			})
		).toBe(true);

		expect(
			shouldAttemptGuestBootstrap({
				search: '?guest=1',
				enableGuestAccess: false,
				hasResolvedUser: false
			})
		).toBe(false);

		expect(
			shouldAttemptGuestBootstrap({
				search: '?guest=1',
				enableGuestAccess: true,
				hasResolvedUser: true
			})
		).toBe(false);
	});

	it('skips auto sign-in when guest bootstrap already succeeded', () => {
		expect(
			shouldRunAutomaticSignIn({
				guestSignInSucceeded: true,
				authTrustedHeader: true,
				authEnabled: true
			})
		).toBe(false);
	});

	it('preserves trusted-header or auth-disabled automatic sign-in on non-guest fallback paths', () => {
		expect(
			shouldRunAutomaticSignIn({
				guestSignInSucceeded: false,
				authTrustedHeader: true,
				authEnabled: true
			})
		).toBe(true);

		expect(
			shouldRunAutomaticSignIn({
				guestSignInSucceeded: false,
				authTrustedHeader: false,
				authEnabled: false
			})
		).toBe(true);
	});
});

describe('root auth bootstrap flow', () => {
	it('restores a valid guest session during reload bootstrap instead of redirecting back to auth', () => {
		expect(
			resolveRootLayoutBootstrap({
				token: 'guest-token',
				sessionUser: { id: 'guest-1' },
				currentPath: '/',
				currentSearch: ''
			})
		).toEqual({
			action: 'restore-session',
			socketAuthTokenSource: 'guest-token'
		});
	});

	it('clears invalid persisted guest state and redirects protected routes to auth', () => {
		expect(
			resolveRootLayoutBootstrap({
				token: 'stale-guest-token',
				sessionUser: null,
				currentPath: '/',
				currentSearch: '?guest=1'
			})
		).toEqual({
			action: 'clear-and-redirect',
			target: '/auth?redirect=%2F%3Fguest%3D1'
		});
	});

	it('keeps blocked guest fallback on the auth page with no token instead of synthesizing a session', () => {
		expect(
			resolveRootLayoutBootstrap({
				token: null,
				sessionUser: null,
				currentPath: '/auth',
				currentSearch: '?guest=1'
			})
		).toEqual({
			action: 'stay-on-auth'
		});
	});
});
