import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { MCPAppResource, MCPToolResult } from '$lib/types/mcpApps';

export const readResource = async (
	token: string,
	serverId: string,
	uri: string
): Promise<MCPAppResource> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/mcp/resource`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			server_id: serverId,
			uri
		})
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err.message || 'Failed to fetch resource';
			return null;
		});

	if (error) {
		throw error;
	}

	return res.resource;
};

export const callTool = async (
	token: string,
	serverId: string,
	toolName: string,
	args: Record<string, unknown> = {}
): Promise<MCPToolResult> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/mcp/tool/call`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			server_id: serverId,
			tool_name: toolName,
			arguments: args
		})
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err.message || 'Failed to call tool';
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const listResources = async (
	token: string,
	serverId: string
): Promise<Array<{ uri: string; name?: string; description?: string; mimeType?: string }>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/mcp/resources`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			server_id: serverId
		})
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err.message || 'Failed to list resources';
			return null;
		});

	if (error) {
		throw error;
	}

	return res.resources || [];
};

export const listPrompts = async (
	token: string,
	serverId: string
): Promise<Array<{ name: string; description?: string }>> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/mcp/prompts`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			server_id: serverId
		})
	})
		.then(async (response) => {
			if (!response.ok) throw await response.json();
			return response.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail || err.message || 'Failed to list prompts';
			return null;
		});

	if (error) {
		throw error;
	}

	return res.prompts || [];
};
