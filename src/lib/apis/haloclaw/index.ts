import { HALOCLAW_API_BASE_URL } from '$lib/constants';
import { parseJsonResponse } from '../response';

// ---------------------------------------------------------------------------
// Global Config
// ---------------------------------------------------------------------------

export const getHaloClawConfig = async (token: string) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('getHaloClawConfig error:', err);
			return null;
		});
	return res;
};

export const updateHaloClawConfig = async (token: string, config: Record<string, any>) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(config)
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('updateHaloClawConfig error:', err);
			throw err.detail || err;
		});
	return res;
};

// ---------------------------------------------------------------------------
// Gateways
// ---------------------------------------------------------------------------

export const getGateways = async (token: string) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('getGateways error:', err);
			return [];
		});
	return res;
};

export const createGateway = async (token: string, data: Record<string, any>) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('createGateway error:', err);
			throw err.detail || err;
		});
	return res;
};

export const updateGateway = async (token: string, id: string, data: Record<string, any>) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways/${id}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('updateGateway error:', err);
			throw err.detail || err;
		});
	return res;
};

export const toggleGateway = async (token: string, id: string, enabled: boolean) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways/${id}/toggle`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ enabled })
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('toggleGateway error:', err);
			throw err.detail || err;
		});
	return res;
};

export const deleteGateway = async (token: string, id: string) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways/${id}`, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('deleteGateway error:', err);
			throw err.detail || err;
		});
	return res;
};

// ---------------------------------------------------------------------------
// External Users
// ---------------------------------------------------------------------------

export const getExternalUsers = async (token: string, gatewayId: string) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways/${gatewayId}/users`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('getExternalUsers error:', err);
			return [];
		});
	return res;
};

export const updateExternalUserModelOverride = async (
	token: string,
	userId: string,
	modelOverride: string | null
) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/users/${userId}/model-override`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ model_override: modelOverride })
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('updateExternalUserModelOverride error:', err);
			throw err.detail || err;
		});
	return res;
};

// ---------------------------------------------------------------------------
// Message Logs
// ---------------------------------------------------------------------------

export const getMessageLogs = async (token: string, gatewayId: string, limit = 100) => {
	const res = await fetch(`${HALOCLAW_API_BASE_URL}/gateways/${gatewayId}/logs?limit=${limit}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('getMessageLogs error:', err);
			return [];
		});
	return res;
};

export const getUserMessageLogs = async (
	token: string,
	gatewayId: string,
	userId: string,
	limit = 200
) => {
	const res = await fetch(
		`${HALOCLAW_API_BASE_URL}/gateways/${gatewayId}/users/${userId}/logs?limit=${limit}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			}
		}
	)
		.then(parseJsonResponse)
		.catch((err) => {
			console.error('getUserMessageLogs error:', err);
			return [];
		});
	return res;
};
