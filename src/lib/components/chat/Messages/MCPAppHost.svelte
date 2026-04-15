<script lang="ts">
	import { onDestroy } from 'svelte';

	import { readResource } from '$lib/apis/mcp';
	import {
		type MCPAppPreviewPayload,
		resolveMCPAppResourceUri,
		resolveMCPAppServerId
	} from '$lib/components/chat/mcpAppPreview';
	import { addApp, closeApp, createAppInstance } from '$lib/stores/mcpApps';
	import type { MCPAppResource } from '$lib/types/mcpApps';

	import MCPAppView from './MCPAppView.svelte';

	export let preview: MCPAppPreviewPayload;

	let mcpResource: MCPAppResource | null = null;
	let mcpInstanceId: string | null = null;
	let mcpLoading = false;
	let mcpError: string | null = null;
	let loadedSignature = '';
	let loadSequence = 0;

	const getResolvedToolName = () => preview?.toolName || preview?.title || 'MCP App';

	const normalizeToolArguments = (value: unknown): Record<string, unknown> =>
		value && typeof value === 'object' && !Array.isArray(value)
			? (value as Record<string, unknown>)
			: {};

	const resetLoadedState = () => {
		if (mcpInstanceId) {
			closeApp(mcpInstanceId);
		}
		mcpResource = null;
		mcpInstanceId = null;
	};

	const ensureResourceLoaded = async () => {
		const toolName = getResolvedToolName();
		const serverId = resolveMCPAppServerId(preview, toolName);
		const resourceUri = resolveMCPAppResourceUri(preview);
		const signature = `${preview?.toolCallId ?? ''}:${serverId ?? ''}:${resourceUri}`;

		if (!preview?.toolCallId || !resourceUri || !serverId) {
			resetLoadedState();
			loadedSignature = '';
			mcpError = 'Missing MCP App resource information';
			mcpLoading = false;
			return;
		}

		if (loadedSignature === signature && (mcpResource || mcpLoading || mcpError)) {
			return;
		}

		resetLoadedState();
		loadedSignature = signature;
		mcpLoading = true;
		mcpError = null;
		const requestId = ++loadSequence;

		try {
			const token = localStorage.token;
			if (!token) {
				throw new Error('No auth token available');
			}

			const resource = await readResource(token, serverId, resourceUri);
			if (requestId !== loadSequence) {
				return;
			}

			mcpResource = resource;
			const instance = createAppInstance({
				serverId,
				toolName,
				resource,
				toolCallId: preview.toolCallId
			});
			mcpInstanceId = instance.instanceId;
			addApp(instance);
		} catch (err) {
			if (requestId !== loadSequence) {
				return;
			}
			console.error('Failed to load MCP App resource:', err);
			mcpError = String(err);
		} finally {
			if (requestId === loadSequence) {
				mcpLoading = false;
			}
		}
	};

	$: if (typeof window !== 'undefined' && preview) {
		void ensureResourceLoaded();
	}

	onDestroy(() => {
		resetLoadedState();
	});
</script>

{#if mcpLoading}
	<div
		class="flex items-center justify-center rounded-xl border border-gray-200 p-4 text-gray-500 dark:border-gray-700"
	>
		<div class="mr-2 h-4 w-4 animate-spin rounded-full border-b-2 border-gray-500"></div>
		<span>Loading MCP App...</span>
	</div>
{:else if mcpError}
	<div
		class="rounded-xl border border-red-200 bg-red-50 p-4 text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
	>
		<strong>Failed to load app:</strong>
		{mcpError}
	</div>
{:else if mcpResource && mcpInstanceId}
	<MCPAppView
		instanceId={mcpInstanceId}
		resource={mcpResource}
		toolName={getResolvedToolName()}
		serverId={resolveMCPAppServerId(preview, getResolvedToolName()) || ''}
		toolArgs={normalizeToolArguments(preview.toolArguments)}
		toolResult={preview.toolResult ?? null}
		toolCallId={preview.toolCallId}
		token={localStorage.token || ''}
	/>
{/if}
