export type MCPAppPreviewPayload = {
	toolCallId: string;
	appId?: string;
	resourceId?: string;
	resourceUri?: string;
	serverId?: string;
	renderUrl?: string;
	content?: string;
	title?: string;
	toolName?: string;
	toolArguments?: unknown;
	toolResult?: unknown;
	structuredContent?: unknown;
};

type ToolCallToken = {
	attributes?: Record<string, string | undefined>;
};

type NormalizePayloadContext = {
	mcpApp?: unknown;
	toolName?: string;
	toolArguments?: unknown;
	toolResult?: unknown;
};

const parseJSON = (value: string): unknown => {
	let current: unknown = value;

	for (let index = 0; index < 2; index += 1) {
		if (typeof current !== 'string') {
			return current;
		}

		try {
			current = JSON.parse(current);
		} catch {
			return current;
		}
	}

	return current;
};

const decodeHtmlEntities = (value: string) =>
	value
		.replaceAll('&quot;', '"')
		.replaceAll('&#39;', "'")
		.replaceAll('&lt;', '<')
		.replaceAll('&gt;', '>')
		.replaceAll('&amp;', '&');

const asObject = (value: unknown): Record<string, unknown> | null =>
	value && typeof value === 'object' && !Array.isArray(value)
		? (value as Record<string, unknown>)
		: null;

const getString = (value: unknown) =>
	typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
		? String(value).trim()
		: '';

const getTagAttribute = (openTag: string, attributeName: string): string | undefined => {
	const match = openTag.match(new RegExp(`\\s${attributeName}="([^"]*)"`, 'i'));
	return match?.[1];
};

const extractServerIdFromRenderUrl = (renderUrl: string): string | undefined => {
	if (!renderUrl) {
		return undefined;
	}

	try {
		const url = new URL(renderUrl, 'http://localhost');
		const serverIdx = url.searchParams.get('server_idx');
		return serverIdx ? serverIdx.trim() : undefined;
	} catch {
		return undefined;
	}
};

const normalizeMCPAppInvocation = (value: unknown) => {
	const payload = asObject(value);
	if (!payload) {
		return null;
	}

	const resourceUri = getString(payload.resourceUri ?? payload.resource_uri);
	const serverId = getString(payload.serverId ?? payload.server_id);
	const title = getString(payload.title ?? payload.name);

	if (!resourceUri && !serverId) {
		return null;
	}

	return {
		...(resourceUri ? { resourceUri } : {}),
		...(serverId ? { serverId } : {}),
		...(title ? { title } : {})
	};
};

const normalizePayload = (
	value: unknown,
	toolCallId: string,
	context: NormalizePayloadContext = {}
): MCPAppPreviewPayload | null => {
	const payload = asObject(value);
	const metadata = asObject(payload?.metadata);
	const invocation = normalizeMCPAppInvocation(context.mcpApp);

	const normalizedToolCallId = getString(
		metadata?.tool_call_id ?? payload?.tool_call_id ?? toolCallId
	);
	if (!normalizedToolCallId) {
		return null;
	}

	const renderUrl = getString(payload?.render_url ?? payload?.renderUrl);
	const content = getString(payload?.content ?? payload?.html ?? payload?.srcdoc);
	const serverId = invocation?.serverId ?? extractServerIdFromRenderUrl(renderUrl);
	const resourceUri = getString(
		invocation?.resourceUri ??
			metadata?.resource_uri ??
			payload?.resource_uri ??
			payload?.resource_id ??
			payload?.resourceId ??
			payload?.app_id ??
			payload?.appId
	);

	const isPreviewable = Boolean((invocation && resourceUri) || renderUrl || content);
	if (!isPreviewable) {
		return null;
	}

	const appId = getString(payload?.app_id ?? payload?.appId ?? resourceUri);
	const resourceId = getString(payload?.resource_id ?? payload?.resourceId ?? resourceUri);
	const title = getString(
		payload?.title ?? payload?.name ?? invocation?.title ?? resourceId ?? appId
	);
	const toolName = getString(context.toolName);
	const resultPayload =
		context.toolResult !== undefined
			? context.toolResult
			: value;
	const structuredContent =
		payload && Object.prototype.hasOwnProperty.call(payload, 'structuredContent')
			? payload.structuredContent
			: undefined;

	return {
		toolCallId: normalizedToolCallId,
		...(appId ? { appId } : {}),
		...(resourceId ? { resourceId } : {}),
		...(resourceUri ? { resourceUri } : {}),
		...(serverId ? { serverId } : {}),
		...(renderUrl ? { renderUrl } : {}),
		...(content ? { content } : {}),
		...(title ? { title } : {}),
		...(toolName ? { toolName } : {}),
		...(context.mcpApp !== undefined && context.toolArguments !== undefined
			? { toolArguments: context.toolArguments }
			: {}),
		...(context.mcpApp !== undefined && resultPayload !== undefined
			? { toolResult: resultPayload }
			: {}),
		...(structuredContent !== undefined ? { structuredContent } : {})
	};
};

export const resolveMCPAppServerId = (
	payload: MCPAppPreviewPayload | null | undefined,
	toolName = ''
) => {
	if (payload?.serverId) {
		return payload.serverId;
	}

	const match = toolName.match(/^mcp_(\d+)__/i);
	return match?.[1];
};

export const resolveMCPAppResourceUri = (payload: MCPAppPreviewPayload | null | undefined) =>
	payload?.resourceUri ?? payload?.resourceId ?? payload?.appId ?? '';

export const getMCPAppPreviewPayload = (token: ToolCallToken | null | undefined) => {
	const attrs = token?.attributes ?? {};
	const toolCallId = getString(attrs.id);
	const result = attrs.result;
	const mcpApp = attrs.mcp_app;

	if (!toolCallId || (!result && !mcpApp)) {
		return null;
	}

	const parsedArguments = attrs.arguments
		? parseJSON(decodeHtmlEntities(attrs.arguments))
		: undefined;
	const parsedResult = result ? parseJSON(decodeHtmlEntities(result)) : undefined;
	const parsedMcpApp = mcpApp ? parseJSON(decodeHtmlEntities(mcpApp)) : undefined;

	return normalizePayload(parsedResult, toolCallId, {
		mcpApp: parsedMcpApp,
		toolName: attrs.name,
		toolArguments: parsedArguments,
		toolResult: parsedResult
	});
};

export const getMCPAppPreviewPayloadsForMessageContent = (
	content: string
): MCPAppPreviewPayload[] => {
	if (!content) {
		return [];
	}

	const matches = content.matchAll(/<details\s+[^>]*type="tool_calls"[^>]*>/gi);
	const payloads: MCPAppPreviewPayload[] = [];
	const seen = new Set<string>();

	for (const match of matches) {
		const openTag = match[0];
		const toolCallId = getTagAttribute(openTag, 'id') ?? '';
		const result = getTagAttribute(openTag, 'result');
		const toolName = decodeHtmlEntities(getTagAttribute(openTag, 'name') ?? '');
		const argumentsValue = getTagAttribute(openTag, 'arguments');
		const mcpApp = getTagAttribute(openTag, 'mcp_app');

		if (!toolCallId || (!result && !mcpApp)) {
			continue;
		}

		const decodedResult = result ? decodeHtmlEntities(result) : undefined;
		const parsedResult = decodedResult ? parseJSON(decodedResult) : undefined;
		const parsedArguments = argumentsValue
			? parseJSON(decodeHtmlEntities(argumentsValue))
			: undefined;
		const parsedMcpApp = mcpApp ? parseJSON(decodeHtmlEntities(mcpApp)) : undefined;

		const payload = normalizePayload(parsedResult, toolCallId, {
			mcpApp: parsedMcpApp,
			toolName,
			toolArguments: parsedArguments,
			toolResult: parsedResult
		});
		if (!payload) {
			continue;
		}

		const identity = `${payload.toolCallId}:${payload.serverId ?? ''}:${
			payload.resourceUri ?? ''
		}:${payload.renderUrl ?? ''}:${payload.content ?? ''}`;
		if (seen.has(identity)) {
			continue;
		}

		seen.add(identity);
		payloads.push(payload);
	}

	return payloads;
};
