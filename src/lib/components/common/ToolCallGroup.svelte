<script lang="ts">
	import { decode } from 'html-entities';
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	const i18n: Writable<any> = getContext('i18n');

	import { slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';

	import ChevronDown from '../icons/ChevronDown.svelte';
	import WrenchSolid from '../icons/WrenchSolid.svelte';
	import Spinner from './Spinner.svelte';
	import MCPAppHost from '../chat/Messages/MCPAppHost.svelte';
	import Markdown from '../chat/Messages/Markdown.svelte';
	import Image from './Image.svelte';
	import GlobeAlt from '../icons/GlobeAlt.svelte';
	import { artifactPreviewTarget, settings, showArtifacts, showControls } from '$lib/stores';
	import { getMCPAppPreviewPayload } from '../chat/mcpAppPreview';

	export let id: string = '';
	export let messageId: string = '';
	export let tokens: any[] = [];

	$: totalCount = tokens.length;
	$: doneCount = tokens.filter((t) => t.attributes?.done === 'true').length;
	$: someExecuting = doneCount < totalCount;

	let expanded = false;
	let selectedIdx: number | null = null;

	function toggleGroup() {
		expanded = !expanded;
		if (!expanded) {
			selectedIdx = null;
		}
	}

	function selectTool(idx: number) {
		selectedIdx = selectedIdx === idx ? null : idx;
	}

	function parseJSONString(str: string): any {
		try {
			return parseJSONString(JSON.parse(str));
		} catch (e) {
			return str;
		}
	}

	function formatJSONString(str: string): string {
		try {
			const parsed = parseJSONString(str);
			if (typeof parsed === 'object') {
				return JSON.stringify(parsed, null, 2);
			} else {
				return `${JSON.stringify(String(parsed))}`;
			}
		} catch (e) {
			return str;
		}
	}

	const SENSITIVE_KEYS =
		/^(password|secret|token|api[_-]?key|auth|credential|private[_-]?key|access[_-]?token)$/i;

	function maskSensitiveFields(str: string): string {
		try {
			const parsed = parseJSONString(str);
			if (typeof parsed === 'object' && parsed !== null) {
				const masked = { ...parsed };
				for (const key of Object.keys(masked)) {
					if (SENSITIVE_KEYS.test(key) && typeof masked[key] === 'string') {
						masked[key] = '••••••••';
					}
				}
				return JSON.stringify(masked, null, 2);
			}
			return formatJSONString(str);
		} catch {
			return formatJSONString(str);
		}
	}

	function isWebSearchTool(name: string): boolean {
		return ['search_web', 'web_search'].includes(name?.toLowerCase() ?? '');
	}

	function isFetchUrlTool(name: string): boolean {
		return ['fetch_url', 'fetch_url_rendered'].includes(name?.toLowerCase() ?? '');
	}

	function isImageGenerationTool(name: string): boolean {
		return ['generate_image', 'edit_image'].includes(name?.toLowerCase() ?? '');
	}

	function parseSearchQuery(argsStr: string): string {
		try {
			const parsed = parseJSONString(argsStr);
			return parsed?.query ?? '';
		} catch {
			return '';
		}
	}

	function parseSearchResults(
		resultStr: string
	): { title: string; link: string; snippet: string }[] | null {
		try {
			const parsed = parseJSONString(resultStr);
			if (Array.isArray(parsed) && parsed.length > 0 && parsed[0]?.link) {
				return parsed;
			}
		} catch {}
		return null;
	}

	function parseFetchResult(
		resultStr: string
	): { url: string; domain: string; title: string; status: string } | null {
		try {
			const parsed = parseJSONString(resultStr);
			if (parsed?.url && parsed?.domain) {
				return parsed;
			}
		} catch {}
		return null;
	}

	$: selectedToken = selectedIdx !== null ? tokens[selectedIdx] : null;
	$: selectedAttrs = selectedToken?.attributes;
	$: selectedDone = selectedAttrs?.done === 'true';
	$: selectedAppPreview = getMCPAppPreviewPayload(selectedToken);
	$: mcpAppDisplayMode = $settings?.mcpAppDisplayMode ?? 'inline';
	$: showInlineMCPApp = Boolean(selectedAppPreview) && mcpAppDisplayMode === 'inline';

	let autoOpenedMCPAppPreviewId = '';

	const findFirstMCPAppPreviewToken = () =>
		tokens.find((token) => token?.attributes?.done === 'true' && getMCPAppPreviewPayload(token));

	function openAppPreview() {
		if (!selectedAppPreview || !selectedAttrs?.id) {
			return;
		}

		artifactPreviewTarget.set({
			messageId,
			type: 'mcp-app',
			toolCallId: selectedAttrs.id,
			...(selectedAppPreview.appId ? { appId: selectedAppPreview.appId } : {}),
			...(selectedAppPreview.resourceId ? { resourceId: selectedAppPreview.resourceId } : {}),
			...(selectedAppPreview.resourceUri ? { resourceUri: selectedAppPreview.resourceUri } : {}),
			...(selectedAppPreview.serverId ? { serverId: selectedAppPreview.serverId } : {}),
			...(selectedAppPreview.renderUrl ? { renderUrl: selectedAppPreview.renderUrl } : {}),
			...(selectedAppPreview.content ? { content: selectedAppPreview.content } : {}),
			...(selectedAppPreview.title ? { title: selectedAppPreview.title } : {}),
			...(selectedAppPreview.toolName ? { toolName: selectedAppPreview.toolName } : {}),
			...(selectedAppPreview.toolArguments !== undefined
				? { toolArguments: selectedAppPreview.toolArguments }
				: {}),
			...(selectedAppPreview.toolResult !== undefined
				? { toolResult: selectedAppPreview.toolResult }
				: {})
		});
		showArtifacts.set(true);
		showControls.set(true);
	}

	function openAppPreviewForToken(token) {
		const preview = getMCPAppPreviewPayload(token);
		const attrs = token?.attributes;
		if (!preview || !attrs?.id) {
			return;
		}

		artifactPreviewTarget.set({
			messageId,
			type: 'mcp-app',
			toolCallId: attrs.id,
			...(preview.appId ? { appId: preview.appId } : {}),
			...(preview.resourceId ? { resourceId: preview.resourceId } : {}),
			...(preview.resourceUri ? { resourceUri: preview.resourceUri } : {}),
			...(preview.serverId ? { serverId: preview.serverId } : {}),
			...(preview.renderUrl ? { renderUrl: preview.renderUrl } : {}),
			...(preview.content ? { content: preview.content } : {}),
			...(preview.title ? { title: preview.title } : {}),
			...(preview.toolName ? { toolName: preview.toolName } : {}),
			...(preview.toolArguments !== undefined ? { toolArguments: preview.toolArguments } : {}),
			...(preview.toolResult !== undefined ? { toolResult: preview.toolResult } : {})
		});
		showArtifacts.set(true);
		showControls.set(true);
	}

	$: if (selectedIdx === null) {
		const firstPreviewToken = findFirstMCPAppPreviewToken();
		if (firstPreviewToken) {
			const previewIdx = tokens.indexOf(firstPreviewToken);
			if (previewIdx >= 0) {
				selectedIdx = previewIdx;
			}
		}
	}

	$: {
		const firstPreviewToken = findFirstMCPAppPreviewToken();
		const preview = firstPreviewToken ? getMCPAppPreviewPayload(firstPreviewToken) : null;
		const previewId = String(firstPreviewToken?.attributes?.id ?? '');
		if (
			typeof window !== 'undefined' &&
			preview &&
			previewId &&
			mcpAppDisplayMode === 'sidebar' &&
			($settings?.detectArtifacts ?? true) &&
			autoOpenedMCPAppPreviewId !== previewId
		) {
			autoOpenedMCPAppPreviewId = previewId;
			window.setTimeout(() => {
				openAppPreviewForToken(firstPreviewToken);
			}, 0);
		}
	}
</script>

<div class="-mx-0.5">
	<!-- Pill button header -->
	<button
		class="text-[13px] font-medium px-3 py-1.5 h-9 rounded-xl
			bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl shadow-sm
			hover:bg-white/80 dark:hover:bg-gray-700/60 transition-all duration-200
			flex items-center gap-1.5
			border border-gray-200/50 dark:border-gray-700/50
			{someExecuting ? 'text-gray-500 dark:text-gray-400' : 'text-gray-600 dark:text-gray-300'}"
		on:click={toggleGroup}
	>
		{#if someExecuting}
			<Spinner className="size-4" />
		{:else}
			<WrenchSolid className="size-4" />
		{/if}

		<span class="translate-y-px {someExecuting ? 'shimmer' : ''}">
			{#if someExecuting}
				正在调用工具{totalCount}次...
			{:else}
				已调用工具{totalCount}次
			{/if}
		</span>

		{#if someExecuting && doneCount > 0}
			<span class="text-gray-400 dark:text-gray-500 tabular-nums">
				{doneCount}/{totalCount}
			</span>
		{/if}

		<div class="shrink-0 transition-transform duration-200" class:rotate-180={expanded}>
			<ChevronDown strokeWidth="3.5" className="size-3" />
		</div>
	</button>

	<!-- Progress bar (only during execution) -->
	{#if someExecuting}
		<div class="mt-1.5 mx-0.5 h-0.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
			<div
				class="h-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-500 ease-out rounded-full"
				style="width: {(doneCount / totalCount) * 100}%"
			/>
		</div>
	{/if}

	<!-- Expanded: chip grid + detail panel -->
	{#if expanded}
		<div class="mt-1.5" transition:slide={{ duration: 200, easing: quintOut }}>
			<!-- Chip flow layout -->
			<div class="flex flex-wrap gap-1.5">
				{#each tokens as toolToken, toolIdx (toolToken.attributes?.id ?? toolIdx)}
					{@const attrs = toolToken.attributes}
					{@const isDone = attrs?.done === 'true'}
					{@const isSelected = selectedIdx === toolIdx}

					<button
						class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs
							transition-all duration-150 outline-none
							{isSelected
							? 'ring-1.5 ring-primary-400/60 dark:ring-primary-500/40 bg-primary-50/60 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
							: isDone
								? 'bg-gray-50 dark:bg-gray-800/60 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/60'
								: 'bg-gray-50 dark:bg-gray-800/60 text-gray-400 dark:text-gray-500'}"
						on:click={() => selectTool(toolIdx)}
					>
						{#if isDone}
							<span class="size-1.5 rounded-full bg-green-500 shrink-0" />
						{:else}
							<Spinner className="size-3" />
						{/if}
						<span class={!isDone ? 'shimmer' : ''}>{attrs?.name ?? 'Unknown'}</span>
					</button>
				{/each}
			</div>

			<!-- Selected tool detail panel -->
			{#if selectedIdx !== null && selectedToken}
				{@const args = decode(selectedAttrs?.arguments ?? '')}
				{@const result = decode(selectedAttrs?.result ?? '')}
				{@const files = parseJSONString(decode(selectedAttrs?.files ?? ''))}
				{@const toolName = selectedAttrs?.name ?? ''}

				<div
					class="mt-2 pl-3 border-l-2 border-primary-300/60 dark:border-primary-600/40"
					transition:slide={{ duration: 200, easing: quintOut }}
				>
					<div class="text-[11px] text-gray-400 dark:text-gray-500 mb-1.5 font-medium">
						{toolName}
					</div>

					{#if selectedAppPreview && selectedDone}
						{#if showInlineMCPApp}
							<MCPAppHost preview={selectedAppPreview} />
						{:else}
							<div class="mb-2">
								<button
									class="inline-flex items-center gap-2 rounded-lg border border-primary-200/60 bg-primary-50/80 px-3 py-2 text-xs font-medium text-primary-700 transition-colors hover:bg-primary-100 dark:border-primary-700/40 dark:bg-primary-900/20 dark:text-primary-300 dark:hover:bg-primary-900/30"
									on:click={openAppPreview}
								>
									<GlobeAlt className="size-3.5 shrink-0" strokeWidth="2" />
									<span>{selectedAppPreview.title || 'Open preview'}</span>
								</button>
							</div>

							<div
								class="rounded-xl border border-primary-200/70 bg-primary-50/70 p-3 dark:border-primary-800/40 dark:bg-primary-950/20"
							>
								<div class="flex items-start justify-between gap-3">
									<div class="min-w-0 flex-1">
										<div
											class="flex items-center gap-2 text-xs font-medium text-primary-700 dark:text-primary-300"
										>
											<GlobeAlt className="size-3.5 shrink-0" strokeWidth="2" />
											<span>MCP App</span>
										</div>
										<div class="mt-1 text-sm font-medium text-gray-800 dark:text-gray-100">
											{selectedAppPreview.title || toolName || 'Open preview'}
										</div>
										<div class="mt-1 break-all text-[11px] text-gray-500 dark:text-gray-400">
											{selectedAppPreview.resourceUri ||
												selectedAppPreview.renderUrl ||
												selectedAppPreview.resourceId ||
												selectedAppPreview.appId}
										</div>
									</div>
									<button
										class="inline-flex items-center gap-2 rounded-lg border border-primary-200/80 bg-white px-3 py-2 text-xs font-medium text-primary-700 transition-colors hover:bg-primary-100 dark:border-primary-700/50 dark:bg-primary-950/30 dark:text-primary-300 dark:hover:bg-primary-900/40"
										type="button"
										on:click={openAppPreview}
									>
										<GlobeAlt className="size-3.5 shrink-0" strokeWidth="2" />
										<span>打开预览</span>
									</button>
								</div>
							</div>
						{/if}
					{:else if isWebSearchTool(toolName) && selectedDone}
						{@const searchQuery = parseSearchQuery(args)}
						{@const searchResults = parseSearchResults(result)}

						{#if searchQuery}
							<div
								class="flex items-center gap-2 px-3 py-2 mb-2 rounded-lg bg-gray-50 dark:bg-gray-800/60 text-sm text-gray-600 dark:text-gray-300"
							>
								<svg
									class="size-3.5 shrink-0 text-gray-400 dark:text-gray-500"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
									stroke-width="2"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
									/>
								</svg>
								<span class="line-clamp-1">{searchQuery}</span>
							</div>
						{/if}

						{#if searchResults && searchResults.length > 0}
							<div
								class="rounded-lg border border-gray-200/50 dark:border-gray-700/50 overflow-hidden"
							>
								{#each searchResults as item, i}
									<a
										href={item.link}
										target="_blank"
										rel="noopener noreferrer"
										class="flex flex-col gap-0.5 px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors no-underline
											{i < searchResults.length - 1 ? 'border-b border-gray-200/50 dark:border-gray-700/50' : ''}"
									>
										<div class="flex items-center gap-2">
											<GlobeAlt
												className="size-3.5 shrink-0 text-gray-400 dark:text-gray-500"
												strokeWidth="2"
											/>
											<span
												class="text-xs font-medium text-gray-700 dark:text-gray-200 line-clamp-1"
											>
												{item.title || item.link}
											</span>
										</div>
										{#if item.snippet}
											<span
												class="text-[11px] text-gray-400 dark:text-gray-500 line-clamp-2 ml-[22px]"
											>
												{item.snippet}
											</span>
										{/if}
									</a>
								{/each}
							</div>
						{:else}
							<Markdown
								id={`${id}-tool-${selectedIdx}-result`}
								content={`> \`\`\`json\n> ${maskSensitiveFields(args)}\n> ${formatJSONString(result)}\n> \`\`\``}
							/>
						{/if}
					{:else if isFetchUrlTool(toolName) && selectedDone}
						{@const fetchResult = parseFetchResult(result)}

						{#if fetchResult}
							<a
								href={fetchResult.url}
								target="_blank"
								rel="noopener noreferrer"
								class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-gray-50 dark:bg-gray-800/60
									hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors no-underline
									border border-gray-200/50 dark:border-gray-700/50"
							>
								<GlobeAlt
									className="size-4 shrink-0 text-gray-400 dark:text-gray-500"
									strokeWidth="2"
								/>
								<div class="flex flex-col gap-0.5 min-w-0 flex-1">
									<span class="text-xs font-medium text-gray-700 dark:text-gray-200 line-clamp-1">
										{fetchResult.title || fetchResult.domain}
									</span>
									<span class="text-[11px] text-gray-400 dark:text-gray-500 line-clamp-1">
										{fetchResult.url}
									</span>
								</div>
								<span
									class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full shrink-0 font-medium
									{fetchResult.status === 'ok'
										? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
										: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400'}"
								>
									{fetchResult.status}
								</span>
							</a>
						{:else}
							<Markdown
								id={`${id}-tool-${selectedIdx}-result`}
								content={`> \`\`\`json\n> ${maskSensitiveFields(args)}\n> ${formatJSONString(result)}\n> \`\`\``}
							/>
						{/if}
					{:else if selectedDone}
						<Markdown
							id={`${id}-tool-${selectedIdx}-result`}
							content={`> \`\`\`json\n> ${maskSensitiveFields(args)}\n> ${formatJSONString(result)}\n> \`\`\``}
						/>
					{:else}
						<Markdown
							id={`${id}-tool-${selectedIdx}-args`}
							content={`> \`\`\`json\n> ${maskSensitiveFields(args)}\n> \`\`\``}
						/>
					{/if}

					{#if selectedDone && !isImageGenerationTool(toolName) && typeof files === 'object'}
						{#each files ?? [] as file}
							{#if typeof file === 'string' && file.startsWith('data:image/')}
								<Image src={file} alt="Image" />
							{:else if file?.type === 'image' && file?.url}
								<Image src={file.url} alt="Image" />
							{/if}
						{/each}
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</div>
