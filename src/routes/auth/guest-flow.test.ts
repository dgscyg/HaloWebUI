import { describe, expect, it } from 'vitest';

const shouldAttemptGuestBootstrap = ({
	search,
	enableGuestAccess,
	hasResolvedUser
}: {
	search: string;
	enableGuestAccess: boolean;
	hasResolvedUser: boolean;
}) => {
	const params = new URLSearchParams(search);
	return params.get('guest') === '1' && enableGuestAccess && !hasResolvedUser;
};

const shouldRunAutomaticSignIn = ({
	guestSignInSucceeded,
	authTrustedHeader,
	authEnabled
}: {
	guestSignInSucceeded: boolean;
	authTrustedHeader: boolean;
	authEnabled: boolean;
}) => {
	if (guestSignInSucceeded) {
		return false;
	}

	return authTrustedHeader || authEnabled === false;
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
