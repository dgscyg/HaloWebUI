import { describe, expect, it } from 'vitest';

import {
	getMCPAppPreviewPayload,
	getMCPAppPreviewPayloadsForMessageContent
} from './mcpAppPreview';

describe('mcpAppPreview', () => {
	it('extracts a previewable MCP app payload from a tool-call token', () => {
		const payload = getMCPAppPreviewPayload({
			attributes: {
				id: 'call_1',
				name: 'mcp_0__lookup',
				result:
					'{"app_id":"resource-1","resource_id":"resource-1","render_url":"https://apps.example/render/1","metadata":{"tool_call_id":"call_1"}}'
			}
		});

		expect(payload).toMatchObject({
			toolCallId: 'call_1',
			appId: 'resource-1',
			resourceId: 'resource-1',
			resourceUri: 'resource-1',
			renderUrl: 'https://apps.example/render/1',
			title: 'resource-1'
		});
	});

	it('decodes HTML-escaped tool-call result payloads from markdown token attributes', () => {
		const payload = getMCPAppPreviewPayload({
			attributes: {
				id: 'call_1',
				name: 'mcp_0__lookup',
				result:
					'{&quot;app_id&quot;:&quot;resource-1&quot;,&quot;render_url&quot;:&quot;https://apps.example/render/1&quot;,&quot;metadata&quot;:{&quot;tool_call_id&quot;:&quot;call_1&quot;}}'
			}
		});

		expect(payload).toMatchObject({
			toolCallId: 'call_1',
			appId: 'resource-1',
			resourceUri: 'resource-1',
			renderUrl: 'https://apps.example/render/1'
		});
	});

	it('rebuilds previewable MCP app payloads from persisted message content', () => {
		const payloads = getMCPAppPreviewPayloadsForMessageContent(`
			<p>hello</p>
			<details type="tool_calls" done="true" id="call_1" name="mcp_0__lookup"
				result="{&quot;app_id&quot;:&quot;resource-1&quot;,&quot;render_url&quot;:&quot;https://apps.example/render/1&quot;,&quot;metadata&quot;:{&quot;tool_call_id&quot;:&quot;call_1&quot;}}">
				<summary>Tool Executed</summary>
			</details>
		`);

		expect(payloads).toEqual([
				expect.objectContaining({
					toolCallId: 'call_1',
					appId: 'resource-1',
					resourceUri: 'resource-1',
					renderUrl: 'https://apps.example/render/1',
					toolName: 'mcp_0__lookup'
				})
			]);
	});

	it('prefers upstream mcp_app attributes and preserves raw tool result payloads', () => {
		const payload = getMCPAppPreviewPayload({
			attributes: {
				id: 'call_1',
				name: 'mcp_0__debug_tool',
				arguments: '{"level":"info"}',
				result:
					'{"content":[{"type":"text","text":"Debug text content #1"}],"structuredContent":{"counter":1},"isError":false}',
				mcp_app: '{"serverId":"0","resourceUri":"ui://debug-tool/mcp-app.html"}'
			}
		});

		expect(payload).toMatchObject({
			toolCallId: 'call_1',
			resourceUri: 'ui://debug-tool/mcp-app.html',
			serverId: '0',
			title: 'ui://debug-tool/mcp-app.html',
			toolName: 'mcp_0__debug_tool',
			toolArguments: {
				level: 'info'
			},
			toolResult: {
				content: [{ type: 'text', text: 'Debug text content #1' }],
				structuredContent: { counter: 1 },
				isError: false
			},
			structuredContent: { counter: 1 }
		});
	});

	it('ignores malformed or non-previewable tool results', () => {
		const payloads = getMCPAppPreviewPayloadsForMessageContent(`
			<details type="tool_calls" done="true" id="call_1" result="{&quot;ok&quot;:true}">
				<summary>Tool Executed</summary>
			</details>
		`);

		expect(payloads).toEqual([]);
	});

	it('ignores regular tool results that only happen to contain a content field', () => {
		const payload = getMCPAppPreviewPayload({
			attributes: {
				id: 'call_1',
				name: 'fetch_url',
				result:
					'{"url":"https://example.com","content":"2026-03-27","title":"Example Domain"}'
			}
		});

		expect(payload).toBeNull();
	});
});
