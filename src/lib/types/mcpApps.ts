export interface McpUiResourceCsp {
	connectDomains?: string[];
	resourceDomains?: string[];
	frameDomains?: string[];
	baseUriDomains?: string[];
}

export interface MCPUIPermissions {
	camera?: Record<string, never>;
	microphone?: Record<string, never>;
	geolocation?: Record<string, never>;
	clipboardWrite?: Record<string, never>;
}

export interface MCPAppResource {
	uri: string;
	content: string;
	mimeType: string;
	csp?: McpUiResourceCsp;
	permissions?: MCPUIPermissions;
}

export type MCPAppDisplayMode = 'inline' | 'fullscreen' | 'pip';

export type MCPAppState = 'loading' | 'initializing' | 'ready' | 'error' | 'closed';

export interface MCPAppInstance {
	instanceId: string;
	serverId: string;
	toolName: string;
	resource: MCPAppResource;
	state: MCPAppState;
	displayMode: MCPAppDisplayMode;
	height: number;
	title: string;
	error?: string;
	toolCallId?: string | number;
	modelContext?: string;
	createdAt: number;
}

export interface MCPAppViewProps {
	instanceId: string;
	resource: MCPAppResource;
	toolName: string;
	serverId: string;
	toolResult?: unknown;
	toolCallId?: string | number;
}

export interface MCPToolResult {
	content: Array<{
		type: 'text' | 'image' | 'audio';
		text?: string;
		data?: string;
		mimeType?: string;
	}>;
	structuredContent?: unknown;
	isError: boolean;
}

export interface MCPAppStateEvent {
	instanceId: string;
	state: MCPAppState;
	error?: string;
}

export interface MCPAppDisplayModeEvent {
	instanceId: string;
	requestedMode: MCPAppDisplayMode;
	actualMode: MCPAppDisplayMode;
}

export interface MCPAppsConfig {
	enabled: boolean;
}

export function buildAllowAttribute(permissions?: MCPUIPermissions): string {
	if (!permissions) {
		return '';
	}

	const allows: string[] = [];
	if (permissions.camera) allows.push('camera');
	if (permissions.microphone) allows.push('microphone');
	if (permissions.geolocation) allows.push('geolocation');
	if (permissions.clipboardWrite) allows.push('clipboard-write');

	return allows.join('; ');
}
