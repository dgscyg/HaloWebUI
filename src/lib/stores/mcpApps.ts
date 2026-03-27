import { derived, writable, type Writable } from 'svelte/store';

import type { MCPAppDisplayMode, MCPAppInstance, MCPAppState } from '$lib/types/mcpApps';

export const mcpApps: Writable<Map<string, MCPAppInstance>> = writable(new Map());

export const fullscreenApp = derived(mcpApps, ($apps) => {
	for (const app of $apps.values()) {
		if (app.displayMode === 'fullscreen') {
			return app;
		}
	}
	return null;
});

export const pipApps = derived(mcpApps, ($apps) =>
	Array.from($apps.values()).filter((app) => app.displayMode === 'pip')
);

export const activeAppCount = derived(mcpApps, ($apps) =>
	Array.from($apps.values()).filter((app) => app.state !== 'closed' && app.state !== 'error')
		.length
);

export function generateInstanceId(): string {
	return `mcp-app-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function createAppInstance(
	params: Pick<MCPAppInstance, 'serverId' | 'toolName' | 'resource' | 'toolCallId'>
): MCPAppInstance {
	return {
		instanceId: generateInstanceId(),
		serverId: params.serverId,
		toolName: params.toolName,
		resource: params.resource,
		state: 'loading',
		displayMode: 'inline',
		height: 400,
		title: params.toolName,
		toolCallId: params.toolCallId,
		createdAt: Date.now()
	};
}

export function addApp(app: MCPAppInstance): void {
	mcpApps.update((apps) => {
		apps.set(app.instanceId, app);
		return apps;
	});
}

export function updateApp(instanceId: string, updates: Partial<MCPAppInstance>): void {
	mcpApps.update((apps) => {
		const app = apps.get(instanceId);
		if (app) {
			apps.set(instanceId, { ...app, ...updates });
		}
		return apps;
	});
}

export function updateAppState(instanceId: string, state: MCPAppState, error?: string): void {
	updateApp(instanceId, { state, error });
}

export function updateAppDisplayMode(instanceId: string, displayMode: MCPAppDisplayMode): void {
	mcpApps.update((apps) => {
		if (displayMode === 'fullscreen') {
			for (const [id, app] of apps) {
				if (app.displayMode === 'fullscreen' && id !== instanceId) {
					apps.set(id, { ...app, displayMode: 'inline' });
				}
			}
		}

		const app = apps.get(instanceId);
		if (app) {
			apps.set(instanceId, { ...app, displayMode });
		}
		return apps;
	});
}

export function updateAppHeight(instanceId: string, height: number): void {
	updateApp(instanceId, { height });
}

export function updateAppTitle(instanceId: string, title: string): void {
	updateApp(instanceId, { title });
}

export function updateAppModelContext(instanceId: string, modelContext: string): void {
	updateApp(instanceId, { modelContext });
}

export function removeApp(instanceId: string): void {
	mcpApps.update((apps) => {
		apps.delete(instanceId);
		return apps;
	});
}

export function closeApp(instanceId: string): void {
	updateAppState(instanceId, 'closed');
	setTimeout(() => removeApp(instanceId), 100);
}

export function getApp(instanceId: string): MCPAppInstance | undefined {
	let result: MCPAppInstance | undefined;
	mcpApps.subscribe((apps) => {
		result = apps.get(instanceId);
	})();
	return result;
}

export function clearApps(): void {
	mcpApps.set(new Map());
}
