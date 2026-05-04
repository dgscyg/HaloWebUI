import { GROK_API_BASE_URL } from '$lib/constants';
import { parseJsonResponse } from '../response';

export const getGrokConfig = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${GROK_API_BASE_URL}/config`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

type GrokConfig = {
	ENABLE_GROK_API: boolean;
	GROK_API_BASE_URLS: string[];
	GROK_API_KEYS: string[];
	GROK_API_CONFIGS: object;
};

export const updateGrokConfig = async (token: string = '', config: GrokConfig) => {
	let error = null;

	const res = await fetch(`${GROK_API_BASE_URL}/config/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			...config
		})
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error(err);
			if ('detail' in err) {
				error = err.detail;
			} else {
				error = 'Server connection failed';
			}
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getGrokModels = async (token: string, urlIdx?: number) => {
	let error = null;

	const res = await fetch(
		`${GROK_API_BASE_URL}/models${typeof urlIdx === 'number' ? `/${urlIdx}` : ''}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	)
		.then(parseJsonResponse)
		.catch((err) => {
			error = `Grok: ${err?.detail ?? err?.error?.message ?? err?.message ?? 'Network Problem'}`;
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};

export const verifyGrokConnection = async (
	token: string = '',
	connection: { url: string; key: string; config?: object }
) => {
	const { url, key, config } = connection;
	if (!url) {
		throw 'Grok: URL is required';
	}

	let error = null;

	const res = await fetch(`${GROK_API_BASE_URL}/verify`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			url,
			key,
			config
		})
	})
		.then(parseJsonResponse)
		.catch((err) => {
			error = `Grok: ${err?.detail ?? err?.error?.message ?? err?.message ?? 'Network Problem'}`;
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};

export const healthCheckGrokConnection = async (
	token: string = '',
	connection: { url: string; key: string; config?: object; model?: string }
) => {
	const { url, key, config, model } = connection;
	if (!url) {
		throw 'Grok: URL is required';
	}

	let error = null;

	const res = await fetch(`${GROK_API_BASE_URL}/health_check`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			url,
			key,
			config,
			model
		})
	})
		.then(parseJsonResponse)
		.catch((err) => {
			error = `Grok: ${err?.detail ?? err?.error?.message ?? err?.message ?? 'Network Problem'}`;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
