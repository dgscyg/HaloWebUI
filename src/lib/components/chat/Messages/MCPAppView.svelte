<script lang="ts">
	import { onDestroy, onMount } from 'svelte';

	import {
		callTool,
		listPrompts,
		listResources,
		readResource as readMcpResource
	} from '$lib/apis/mcp';
	import {
		updateAppDisplayMode,
		updateAppHeight,
		updateAppModelContext,
		updateAppState
	} from '$lib/stores/mcpApps';
	import type { MCPAppDisplayMode, MCPAppResource } from '$lib/types/mcpApps';
	import { buildAllowAttribute } from '$lib/types/mcpApps';

	import { AppBridge, PostMessageTransport } from '@modelcontextprotocol/ext-apps/app-bridge';
	import type { CallToolResult, TextContent } from '@modelcontextprotocol/sdk/types.js';

	export let instanceId: string;
	export let resource: MCPAppResource;
	export let toolName: string;
	export let serverId: string;
	export let toolArgs: Record<string, unknown> = {};
	export let toolResult: unknown = null;
	export let toolCallId: string | number | undefined = undefined;
	export let token: string = '';

	let bridge: AppBridge | null = null;
	let outerIframe: HTMLIFrameElement | null = null;
	let state: 'loading' | 'initializing' | 'ready' | 'error' | 'closed' = 'loading';
	let displayMode: MCPAppDisplayMode = 'inline';
	let height = 400;
	let title = toolName;
	let error: string | null = null;
	let initialized = false;
	let lastSentToolResultSignature = '';

	let theme: 'light' | 'dark' = 'dark';
	let locale = 'en-US';
	let timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
	let containerWidth = 600;
	let containerMaxHeight = 600;

	function detectTheme(): 'light' | 'dark' {
		if (typeof document !== 'undefined') {
			return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
		}
		return 'dark';
	}

	$: {
		const detectedTheme = detectTheme();
		if (detectedTheme !== theme) {
			theme = detectedTheme;
			if (bridge && initialized) {
				bridge.setHostContext({ theme });
			}
		}
	}

	const hostCapabilities = {
		openLinks: {},
		serverResources: { listChanged: false },
		serverTools: { listChanged: false },
		message: {
			text: {},
			image: {},
			audio: {},
			resource: {},
			resourceLink: {},
			structuredContent: {}
		},
		logging: {},
		updateModelContext: {
			text: {},
			image: {},
			audio: {},
			resource: {},
			resourceLink: {},
			structuredContent: {}
		}
	};

	const hostInfo = {
		name: 'HaloWebUI',
		version: '1.0.0'
	};

	function getHostContext() {
		return {
			theme,
			locale,
			timeZone,
			displayMode,
			availableDisplayModes: ['inline', 'fullscreen', 'pip'] as MCPAppDisplayMode[],
			containerDimensions: {
				width: containerWidth,
				maxHeight: containerMaxHeight
			},
			platform: 'web' as const
		};
	}

	function createSandboxProxyScript(): string {
		const script = `<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<style>
		* { margin: 0; padding: 0; box-sizing: border-box; }
		html, body { width: 100%; height: 100%; overflow: hidden; }
		iframe { width: 100%; height: 100%; border: none; }
	</style>
</head>
<body>
<script>
let innerFrame = null;

function buildCspString(cspObj) {
	if (!cspObj) {
		return "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' data:; connect-src 'none'";
	}

	let parts = ["default-src 'none'"];

	const resourceDomains = (cspObj.resourceDomains || []).join(' ');
	const connectDomains = (cspObj.connectDomains || []).join(' ');
	const frameDomains = (cspObj.frameDomains || []).join(' ');
	const baseUriDomains = (cspObj.baseUriDomains || []).join(' ');

	parts.push("script-src 'self' 'unsafe-inline'" + (resourceDomains ? ' ' + resourceDomains : ''));
	parts.push("style-src 'self' 'unsafe-inline'" + (resourceDomains ? ' ' + resourceDomains : ''));
	parts.push("img-src 'self' data:" + (resourceDomains ? ' ' + resourceDomains : ''));
	parts.push("font-src 'self'" + (resourceDomains ? ' ' + resourceDomains : ''));
	parts.push("media-src 'self' data:" + (resourceDomains ? ' ' + resourceDomains : ''));
	parts.push("connect-src" + (connectDomains ? ' ' + connectDomains : " 'none'"));
	parts.push("frame-src" + (frameDomains ? ' ' + frameDomains : " 'none'"));
	parts.push("object-src 'none'");
	parts.push("base-uri" + (baseUriDomains ? ' ' + baseUriDomains : " 'self'"));

	return parts.join('; ');
}

function buildAllowAttr(permissions) {
	if (!permissions) return '';
	const perms = [];
	if (permissions.camera) perms.push('camera');
	if (permissions.microphone) perms.push('microphone');
	if (permissions.geolocation) perms.push('geolocation');
	if (permissions.clipboardWrite) perms.push('clipboard-write');
	return perms.join('; ');
}

window.addEventListener('message', (event) => {
	if (event.source === window.parent) {
		if (event.data?.method === 'ui/notifications/sandbox-resource-ready') {
			const params = event.data.params || {};
			const html = params.html || '';
			const sandbox = params.sandbox || 'allow-scripts allow-same-origin';
			const cspString = buildCspString(params.csp);
			const allowAttr = buildAllowAttr(params.permissions);

			innerFrame = document.createElement('iframe');
			innerFrame.sandbox = sandbox;
			if (allowAttr) innerFrame.allow = allowAttr;

			let finalHtml = html;
			const metaTag = '<meta http-equiv="Content-Security-Policy" content="' + cspString + '">';
			if (finalHtml.includes('<head>')) {
				finalHtml = finalHtml.replace('<head>', '<head>' + metaTag);
			} else if (finalHtml.includes('<html>')) {
				finalHtml = finalHtml.replace('<html>', '<html><head>' + metaTag + '</head>');
			} else {
				finalHtml = '<head>' + metaTag + '</head>' + finalHtml;
			}

			const blob = new Blob([finalHtml], { type: 'text/html' });
			innerFrame.src = URL.createObjectURL(blob);
			document.body.appendChild(innerFrame);
		} else if (innerFrame && innerFrame.contentWindow) {
			innerFrame.contentWindow.postMessage(event.data, '*');
		}
	} else if (innerFrame && event.source === innerFrame.contentWindow) {
		window.parent.postMessage(event.data, '*');
	}
});

window.parent.postMessage({
	jsonrpc: '2.0',
	method: 'ui/notifications/sandbox-proxy-ready',
	params: {}
}, '*');
<\/script>
</body>
</html>`;
		return URL.createObjectURL(new Blob([script], { type: 'text/html' }));
	}

	function getContainerDimensions() {
		switch (displayMode) {
			case 'fullscreen':
				return {
					width: window.innerWidth,
					height: window.innerHeight,
					maxWidth: window.innerWidth,
					maxHeight: window.innerHeight
				};
			case 'pip':
				return {
					width: 400,
					maxHeight: 300
				};
			default:
				return {
					width: containerWidth,
					maxHeight: containerMaxHeight
				};
		}
	}

	function formatToolResult(result: unknown): CallToolResult {
		if (
			result &&
			typeof result === 'object' &&
			'content' in result &&
			Array.isArray((result as CallToolResult).content)
		) {
			const content = (result as CallToolResult).content.map((item) => ({
				...item,
				annotations: (item as Record<string, unknown>).annotations ?? {}
			}));
			return {
				...(result as CallToolResult),
				content,
				structuredContent: (result as Record<string, unknown>).structuredContent ?? {}
			} as CallToolResult;
		}

		const textContent: TextContent = {
			type: 'text',
			text: typeof result === 'string' ? result : JSON.stringify(result),
			annotations: {}
		};

		return {
			content: [textContent],
			structuredContent: {},
			isError: false
		} as CallToolResult;
	}

	function getToolResultSignature(result: unknown) {
		try {
			return JSON.stringify(result ?? null);
		} catch {
			return String(result ?? '');
		}
	}

	function sendToolResult(result: unknown, { force = false }: { force?: boolean } = {}) {
		if (!bridge || !initialized) {
			console.warn('MCPAppView: Cannot send tool result, bridge not initialized');
			return;
		}

		const nextSignature = getToolResultSignature(result);
		if (!force && nextSignature === lastSentToolResultSignature) {
			return;
		}

		const mcpResult = formatToolResult(result);
		lastSentToolResultSignature = nextSignature;
		bridge.sendToolResult(mcpResult);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && displayMode !== 'inline') {
			displayMode = 'inline';
			updateAppDisplayMode(instanceId, displayMode);
			if (bridge) {
				bridge.setHostContext({
					displayMode,
					containerDimensions: getContainerDimensions()
				});
			}
		}
	}

	async function cleanup() {
		if (bridge && initialized && outerIframe?.isConnected) {
			try {
				await bridge.teardownResource({});
			} catch (err) {
				const message = String(err ?? '');
				if (!message.includes('Request timed out')) {
					console.warn('MCPAppView: Teardown failed:', err);
				}
			}
		}
		bridge = null;
	}

	onMount(async () => {
		const proxyUrl = createSandboxProxyScript();

		outerIframe = document.createElement('iframe');
		outerIframe.src = proxyUrl;
		outerIframe.sandbox = 'allow-scripts allow-same-origin';
		outerIframe.style.width = '100%';
		outerIframe.style.height = `${height}px`;
		outerIframe.style.border = 'none';
		outerIframe.style.borderRadius = '0.5rem';

		if (resource.permissions) {
			const allow = buildAllowAttribute(resource.permissions);
			if (allow) {
				outerIframe.allow = allow;
			}
		}

		const container = document.getElementById(`mcp-app-container-${instanceId}`);
		if (!container) {
			error = 'MCP app container not found';
			state = 'error';
			updateAppState(instanceId, 'error', error);
			return;
		}

		try {
			bridge = new AppBridge(null, hostInfo, hostCapabilities, {
				hostContext: getHostContext()
			});

			bridge.oninitialized = () => {
				initialized = true;
				state = 'ready';
				updateAppState(instanceId, 'ready');
				bridge?.sendToolInput({ arguments: toolArgs });
				if (toolResult !== null) {
					sendToolResult(toolResult, { force: true });
				}
			};

			bridge.onsandboxready = () => {
				state = 'initializing';
				updateAppState(instanceId, 'initializing');
				bridge?.sendSandboxResourceReady({
					html: resource.content,
					sandbox: 'allow-scripts allow-same-origin',
					csp: resource.csp,
					permissions: resource.permissions
				});
			};

			bridge.onsizechange = ({ height: newHeight }) => {
				if (newHeight != null && newHeight > 0) {
					height = newHeight;
					updateAppHeight(instanceId, height);
				}
			};

			bridge.onopenlink = async ({ url }) => {
				try {
					window.open(url, '_blank', 'noopener,noreferrer');
					return {};
				} catch (err) {
					console.error('MCPAppView: Failed to open link:', err);
					return { isError: true };
				}
			};

			bridge.onrequestdisplaymode = async ({ mode }) => {
				const availableModes: MCPAppDisplayMode[] = ['inline', 'fullscreen', 'pip'];
				if (availableModes.includes(mode as MCPAppDisplayMode)) {
					displayMode = mode as MCPAppDisplayMode;
					updateAppDisplayMode(instanceId, displayMode);
					bridge?.setHostContext({
						displayMode,
						containerDimensions: getContainerDimensions()
					});
				}
				return { mode: displayMode };
			};

			bridge.onloggingmessage = ({ level, logger, data }) => {
				const logFn = level === 'error' ? console.error : console.log;
				logFn(`[MCP App${logger ? ` - ${logger}` : ''}] ${level}:`, data);
			};

			bridge.onmessage = async (params) => {
				console.info('MCPAppView: App message', {
					instanceId,
					toolCallId,
					params
				});
				return {};
			};

			bridge.oncalltool = async (params): Promise<CallToolResult> => {
				try {
					const result = await callTool(token, serverId, params.name, params.arguments || {});
					return formatToolResult(result);
				} catch (err) {
					console.error('MCPAppView: Tool call failed:', err);
					const errorContent: TextContent = {
						type: 'text',
						text: String(err),
						annotations: {}
					};
					return {
						content: [errorContent],
						structuredContent: {},
						isError: true
					} as CallToolResult;
				}
			};

			bridge.onlistresources = async (_params) => {
				const resources = await listResources(token, serverId);
				return { resources };
			};

			bridge.onlistresourcetemplates = async (_params) => {
				return { resourceTemplates: [] };
			};

			bridge.onreadresource = async (params) => {
				const readResult = await readMcpResource(token, serverId, params.uri);
				return {
					contents: [
						{
							uri: readResult.uri,
							mimeType: readResult.mimeType,
							text: readResult.content
						}
					]
				};
			};

			bridge.onlistprompts = async (_params) => {
				const prompts = await listPrompts(token, serverId);
				return { prompts };
			};

			bridge.onupdatemodelcontext = async (params: {
				content?: Array<{ type: string; text?: string }>;
				structuredContent?: Record<string, unknown>;
			}) => {
				const content = params.content || [];
				const textParts = content
					.filter((item) => item.type === 'text' && item.text)
					.map((item) => item.text as string);
				const structuredContext =
					params.structuredContent && Object.keys(params.structuredContent).length > 0
						? JSON.stringify(params.structuredContent, null, 2)
						: '';
				const contextText = [textParts.join('\n'), structuredContext].filter(Boolean).join('\n');
				if (contextText) {
					updateAppModelContext(instanceId, contextText);
				}
				return {};
			};

			container.appendChild(outerIframe);

			const transport = new PostMessageTransport(
				outerIframe.contentWindow!,
				outerIframe.contentWindow!
			);

			await bridge.connect(transport);
		} catch (err) {
			console.error('MCPAppView: Failed to initialize bridge:', err);
			error = String(err);
			state = 'error';
			updateAppState(instanceId, 'error', error);
		}

		window.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		void cleanup();
		window.removeEventListener('keydown', handleKeydown);
	});

	$: if (toolResult !== null && initialized && bridge) {
		sendToolResult(toolResult);
	}

	$: if (outerIframe) {
		outerIframe.style.height = `${height}px`;
	}
</script>

<div
	id="mcp-app-container-{instanceId}"
	class="mcp-app-container {displayMode === 'fullscreen'
		? 'mcp-app-fullscreen'
		: ''} {displayMode === 'pip' ? 'mcp-app-pip' : ''}"
	class:mcp-app-inline={displayMode === 'inline'}
>
	{#if state === 'loading' || state === 'initializing'}
		<div class="mcp-app-loading flex items-center justify-center p-4 text-gray-500">
			<div class="mr-2 h-6 w-6 animate-spin rounded-full border-b-2 border-gray-500"></div>
			<span>{state === 'loading' ? 'Loading app...' : 'Initializing...'}</span>
		</div>
	{/if}

	{#if state === 'error'}
		<div
			class="mcp-app-error rounded-lg bg-red-100 p-4 text-red-700 dark:bg-red-900 dark:text-red-200"
		>
			<strong>Error:</strong>
			{error}
		</div>
	{/if}

	{#if displayMode === 'fullscreen'}
		<div
			class="mcp-app-fullscreen-header flex items-center justify-between bg-gray-800 p-2 text-white"
		>
			<span class="font-semibold">{title}</span>
			<button
				type="button"
				class="rounded p-1 hover:bg-gray-700"
				aria-label="Close fullscreen"
				on:click={() => {
					displayMode = 'inline';
					updateAppDisplayMode(instanceId, displayMode);
					if (bridge) {
						bridge.setHostContext({
							displayMode,
							containerDimensions: getContainerDimensions()
						});
					}
				}}
			>
				<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>
		</div>
	{/if}
</div>

<style>
	.mcp-app-container {
		position: relative;
		min-height: 100px;
		overflow: hidden;
		border: 1px solid var(--border-color, #e5e7eb);
		border-radius: 0.5rem;
		background: var(--bg-color, #ffffff);
	}

	:global(.dark) .mcp-app-container {
		--border-color: #374151;
		--bg-color: #1f2937;
	}

	.mcp-app-fullscreen {
		position: fixed;
		inset: 0;
		z-index: 9999;
		border: none;
		border-radius: 0;
	}

	.mcp-app-fullscreen :global(iframe) {
		height: calc(100% - 40px) !important;
	}

	.mcp-app-pip {
		position: fixed;
		right: 1rem;
		bottom: 1rem;
		z-index: 9998;
		width: 400px;
		max-height: 300px;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
	}

	.mcp-app-loading {
		min-height: 100px;
	}

	.mcp-app-fullscreen-header {
		height: 40px;
	}
</style>
