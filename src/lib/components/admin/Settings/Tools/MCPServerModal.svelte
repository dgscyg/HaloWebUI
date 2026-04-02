<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';

	const i18n: Writable<any> = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import CollapsibleSection from '$lib/components/common/CollapsibleSection.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import HaloSelect from '$lib/components/common/HaloSelect.svelte';

	import { verifyMCPServerConnection } from '$lib/apis/configs';

	export let show = false;
	export let connection: any = null;
	export let onSubmit: (connection: any) => Promise<void> = async () => {};

	// Tab state
	let activeTab: 'manual' | 'presets' = 'presets';

	// Form fields
	let name = '';
	let url = '';
	let description = '';
	let auth_type = 'none';
	let key = '';
	let enable = true;

	// Verify state
	let loading = false;
	let verifyStatus: 'idle' | 'loading' | 'success' | 'error' = 'idle';
	let verifyResult: { server_info: any; tool_count: number; tools: any[] } | null = null;
	let verifyError = '';
	let showAllTools = false;

	// Presets
	interface MCPPreset {
		id: string;
		name: string;
		description: string;
		icon: string;
		category: 'hosted' | 'self-hosted';
		url_template: string;
		auth_type: string;
		requires_key: boolean;
		setup_hint: string;
		doc_url?: string;
	}

	const MCP_PRESETS: MCPPreset[] = [
		{
			id: 'composio',
			name: 'Composio',
			description: '200+ 应用集成 (GitHub, Slack, Gmail, Jira 等)',
			icon: '🔗',
			category: 'hosted',
			url_template: 'https://mcp.composio.dev',
			auth_type: 'bearer',
			requires_key: true,
			setup_hint: '在 composio.dev 注册获取 API Key',
			doc_url: 'https://docs.composio.dev'
		},
		{
			id: 'smithery',
			name: 'Smithery',
			description: 'MCP 服务器托管平台，支持 fetch/memory/search 等',
			icon: '🛠️',
			category: 'hosted',
			url_template: 'https://server.smithery.ai/{server-name}/mcp',
			auth_type: 'bearer',
			requires_key: true,
			setup_hint: '在 smithery.ai 注册，选择 MCP 服务器获取端点和 Key',
			doc_url: 'https://smithery.ai'
		},
		{
			id: 'zapier',
			name: 'Zapier MCP',
			description: '工作流自动化，连接 7000+ 应用',
			icon: '⚡',
			category: 'hosted',
			url_template: 'https://actions.zapier.com/mcp/actions',
			auth_type: 'bearer',
			requires_key: true,
			setup_hint: '在 Zapier 设置中启用 MCP 并获取 Access Token',
			doc_url: 'https://actions.zapier.com'
		},
		{
			id: 'local-bridge',
			name: '本地 stdio 桥接',
			description: '将 fetch/time/memory 等 stdio MCP 服务器转为 HTTP',
			icon: '🖥️',
			category: 'self-hosted',
			url_template: 'http://localhost:8808/mcp',
			auth_type: 'none',
			requires_key: false,
			setup_hint:
				'npx @anthropic-ai/mcp-proxy --transport http --port 8808 -- npx @anthropic-ai/mcp-server-fetch'
		}
	];

	const init = () => {
		verifyStatus = 'idle';
		verifyResult = null;
		verifyError = '';
		showAllTools = false;

		if (!connection) {
			activeTab = 'presets';
			name = '';
			url = '';
			description = '';
			auth_type = 'none';
			key = '';
			enable = true;
			return;
		}

		activeTab = 'manual';
		name = connection.name ?? '';
		url = connection.url ?? '';
		description = connection.description ?? '';
		auth_type = connection.auth_type ?? 'none';
		key = connection.key ?? '';
		enable = connection.config?.enable ?? connection.enabled ?? true;

		// Restore cached verify data
		if (connection.server_info) {
			verifyStatus = 'success';
			verifyResult = {
				server_info: connection.server_info,
				tool_count: connection.tool_count ?? 0,
				tools: []
			};
		}
	};

	$: if (show) {
		init();
	}

	onMount(() => {
		init();
	});

	const applyPreset = (preset: MCPPreset) => {
		name = preset.name;
		url = preset.url_template;
		description = preset.description;
		auth_type = preset.auth_type;
		key = '';
		activeTab = 'manual';
		verifyStatus = 'idle';
		verifyResult = null;
	};

	const verifyHandler = async () => {
		if (url.trim() === '') {
			toast.error($i18n.t('Please enter a valid URL'));
			return;
		}

		loading = true;
		verifyStatus = 'loading';
		verifyError = '';

		const res = await verifyMCPServerConnection(localStorage.token, {
			url: url.trim().replace(/\/$/, ''),
			auth_type,
			key: auth_type === 'bearer' || auth_type === 'oauth21' ? key : undefined,
			config: { enable }
		}).catch((err) => {
			verifyStatus = 'error';
			verifyError = err?.message || err?.detail || $i18n.t('Connection failed');
			return null;
		});

		loading = false;

		if (res) {
			verifyStatus = 'success';
			verifyResult = {
				server_info: res.server_info || {},
				tool_count: res.tool_count ?? 0,
				tools: res.tools || []
			};
			// Auto-fill name from server info if empty
			if (!name.trim() && res.server_info?.name) {
				name = res.server_info.name;
			}
			toast.success(
				$i18n.t('Connection successful') +
					(res.tool_count !== undefined ? ` (${res.tool_count} ${$i18n.t('tools')})` : '')
			);
		}
	};

	const submitHandler = async () => {
		if (url.trim() === '') {
			toast.error($i18n.t('Please enter a valid URL'));
			return;
		}

		loading = true;
		const nextMCPApps =
			connection?.mcp_apps && typeof connection.mcp_apps === 'object'
				? { enabled: true, ...connection.mcp_apps }
				: { enabled: true };

		const next: any = {
			url: url.trim().replace(/\/$/, ''),
			name: name.trim() || undefined,
			description: description.trim() || undefined,
			auth_type,
			key: auth_type === 'bearer' || auth_type === 'oauth21' ? key : undefined,
			config: { enable },
			mcp_apps: nextMCPApps,
			server_info: verifyResult?.server_info || undefined,
			tool_count: verifyResult?.tool_count ?? undefined
		};

		await onSubmit(next);

		loading = false;
		show = false;
	};
</script>

<Modal size="md" bind:show>
	<div>
		<!-- Header -->
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 pb-2">
			<div class="text-lg font-medium self-center font-primary">
				{connection ? $i18n.t('Edit Connection') : $i18n.t('Add Connection')}
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
				type="button"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<!-- Tabs (only show when adding, not editing) -->
		{#if !connection}
			<div class="flex px-5 gap-1 border-b border-gray-100 dark:border-gray-800">
				<button
					type="button"
					class="px-4 py-2 text-sm font-medium transition-colors {activeTab === 'presets'
						? 'text-black dark:text-white border-b-2 border-black dark:border-white'
						: 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					on:click={() => (activeTab = 'presets')}
				>
					{$i18n.t('推荐服务器')}
				</button>
				<button
					type="button"
					class="px-4 py-2 text-sm font-medium transition-colors {activeTab === 'manual'
						? 'text-black dark:text-white border-b-2 border-black dark:border-white'
						: 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					on:click={() => (activeTab = 'manual')}
				>
					{$i18n.t('手动配置')}
				</button>
			</div>
		{/if}

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<!-- Manual Tab -->
			{#if activeTab === 'manual'}
				<form
					class="flex flex-col w-full"
					on:submit|preventDefault={() => {
						submitHandler();
					}}
				>
					<div class="space-y-3 mt-3">
						<!-- Name -->
						<div>
							<div class="text-xs text-gray-500 mb-1">{$i18n.t('服务器名称（可选）')}</div>
							<input
								class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden border-b border-gray-200 dark:border-gray-700 pb-1"
								type="text"
								bind:value={name}
								placeholder={$i18n.t('例如: My MCP Server')}
								autocomplete="off"
							/>
						</div>

						<!-- URL + Enable + Verify -->
						<div>
							<div class="flex items-center justify-between mb-1">
								<div class="text-xs text-gray-500">{$i18n.t('URL')}</div>
								<Tooltip content={enable ? $i18n.t('Enabled') : $i18n.t('Disabled')}>
									<Switch bind:state={enable} />
								</Tooltip>
							</div>
							<div class="flex gap-2 items-center">
								<input
									class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden border-b border-gray-200 dark:border-gray-700 pb-1"
									type="text"
									bind:value={url}
									placeholder={$i18n.t('API Base URL')}
									autocomplete="off"
									required
								/>
								<Tooltip content={$i18n.t('Verify Connection')} className="shrink-0">
									<button
										class="self-center p-1.5 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition {verifyStatus ===
										'loading'
											? 'animate-spin'
											: ''}"
										on:click={() => {
											verifyHandler();
										}}
										type="button"
										disabled={loading}
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 20 20"
											fill="currentColor"
											class="w-4 h-4"
										>
											<path
												fill-rule="evenodd"
												d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
												clip-rule="evenodd"
											/>
										</svg>
									</button>
								</Tooltip>
							</div>
						</div>

						<!-- Description -->
						<div>
							<div class="text-xs text-gray-500 mb-1">{$i18n.t('描述（可选）')}</div>
							<input
								class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden border-b border-gray-200 dark:border-gray-700 pb-1"
								type="text"
								bind:value={description}
								placeholder={$i18n.t('简要描述此服务器的用途')}
								autocomplete="off"
							/>
						</div>

						<!-- Advanced (Auth) -->
						<CollapsibleSection
							title={$i18n.t('Advanced')}
							open={auth_type !== 'none'}
							className="mt-1"
						>
							<div class="space-y-3">
								<div>
									<div class="text-xs text-gray-500">{$i18n.t('Auth')}</div>
									<HaloSelect
										bind:value={auth_type}
										options={[
											{ value: 'none', label: 'None' },
											{ value: 'bearer', label: 'Bearer' },
											{ value: 'session', label: 'Session' },
											{ value: 'oauth21', label: 'OAuth 2.1' }
										]}
										className="w-fit"
									/>
								</div>

								{#if auth_type === 'bearer' || auth_type === 'oauth21'}
									<div>
										<div class="text-xs text-gray-500">{$i18n.t('Key')}</div>
										<SensitiveInput bind:value={key} />
									</div>
								{/if}
							</div>
						</CollapsibleSection>

						<!-- Verify Result -->
						{#if verifyStatus === 'loading'}
							<div
								class="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50 rounded-lg"
							>
								<svg
									class="animate-spin h-4 w-4 text-blue-500"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
								>
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
									></path>
								</svg>
								<span class="text-sm text-blue-700 dark:text-blue-300">{$i18n.t('验证中...')}</span>
							</div>
						{:else if verifyStatus === 'success' && verifyResult}
							<div
								class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50 rounded-lg space-y-2"
							>
								<div class="flex items-center gap-2">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="w-4 h-4 text-green-600 dark:text-green-400"
									>
										<path
											fill-rule="evenodd"
											d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
											clip-rule="evenodd"
										/>
									</svg>
									<span class="text-sm font-medium text-green-800 dark:text-green-300">
										{verifyResult.server_info?.name || 'MCP Server'}
										{#if verifyResult.server_info?.version}
											<span class="text-xs font-normal opacity-70"
												>v{verifyResult.server_info.version}</span
											>
										{/if}
									</span>
									<span
										class="ml-auto px-2 py-0.5 text-xs rounded-full bg-green-100 dark:bg-green-800/40 text-green-700 dark:text-green-300"
									>
										{verifyResult.tool_count}
										{$i18n.t('个工具')}
									</span>
								</div>

								<!-- Tool list -->
								{#if verifyResult.tools && verifyResult.tools.length > 0}
									<div class="space-y-1 mt-2">
										{#each showAllTools ? verifyResult.tools : verifyResult.tools.slice(0, 5) as tool}
											<div class="flex items-start gap-2 text-xs">
												<span class="font-mono text-green-700 dark:text-green-400 shrink-0"
													>{tool.name}</span
												>
												{#if tool.description}
													<span class="text-gray-500 truncate">{tool.description}</span>
												{/if}
											</div>
										{/each}
										{#if verifyResult.tools.length > 5 && !showAllTools}
											<button
												type="button"
												class="text-xs text-green-600 dark:text-green-400 hover:underline"
												on:click={() => (showAllTools = true)}
											>
												{$i18n.t('显示全部')} ({verifyResult.tools.length})
											</button>
										{/if}
									</div>
								{/if}
							</div>
						{:else if verifyStatus === 'error'}
							<div
								class="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-lg"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-4 h-4 text-red-500 shrink-0"
								>
									<path
										fill-rule="evenodd"
										d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
										clip-rule="evenodd"
									/>
								</svg>
								<span class="text-sm text-red-700 dark:text-red-300"
									>{verifyError || $i18n.t('Connection failed')}</span
								>
							</div>
						{/if}
					</div>

					<div class="flex justify-end pt-4 text-sm font-medium">
						<button
							class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full {loading
								? ' cursor-not-allowed'
								: ''}"
							type="submit"
							disabled={loading}
						>
							{$i18n.t('Save')}
						</button>
					</div>
				</form>

				<!-- Presets Tab -->
			{:else if activeTab === 'presets'}
				<div class="space-y-4 mt-3">
					<!-- Hosted Services -->
					<div>
						<div
							class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2"
						>
							{$i18n.t('托管服务')}
						</div>
						<div class="space-y-2">
							{#each MCP_PRESETS.filter((p) => p.category === 'hosted') as preset}
								<button
									type="button"
									class="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-850 transition group"
									on:click={() => applyPreset(preset)}
								>
									<div class="flex items-start gap-3">
										<span class="text-xl mt-0.5">{preset.icon}</span>
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2">
												<span class="text-sm font-medium text-gray-900 dark:text-gray-100"
													>{preset.name}</span
												>
												{#if preset.requires_key}
													<span
														class="px-1.5 py-0.5 text-[10px] rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300"
													>
														{$i18n.t('需要 API Key')}
													</span>
												{/if}
											</div>
											<div class="text-xs text-gray-500 mt-0.5">{preset.description}</div>
											<div class="text-xs text-gray-400 mt-1 flex items-center gap-1">
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 16 16"
													fill="currentColor"
													class="w-3 h-3"
												>
													<path
														fill-rule="evenodd"
														d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
														clip-rule="evenodd"
													/>
												</svg>
												{preset.setup_hint}
											</div>
										</div>
										<div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-5 h-5 text-gray-400"
											>
												<path
													fill-rule="evenodd"
													d="M3 10a.75.75 0 01.75-.75h10.638l-3.96-4.158a.75.75 0 011.08-1.04l5.25 5.5a.75.75 0 010 1.04l-5.25 5.5a.75.75 0 11-1.08-1.04l3.96-4.158H3.75A.75.75 0 013 10z"
													clip-rule="evenodd"
												/>
											</svg>
										</div>
									</div>
								</button>
							{/each}
						</div>
					</div>

					<!-- Self-hosted -->
					<div>
						<div
							class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2"
						>
							{$i18n.t('自托管')}
						</div>
						<div class="space-y-2">
							{#each MCP_PRESETS.filter((p) => p.category === 'self-hosted') as preset}
								<button
									type="button"
									class="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-850 transition group"
									on:click={() => applyPreset(preset)}
								>
									<div class="flex items-start gap-3">
										<span class="text-xl mt-0.5">{preset.icon}</span>
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2">
												<span class="text-sm font-medium text-gray-900 dark:text-gray-100"
													>{preset.name}</span
												>
												<span
													class="px-1.5 py-0.5 text-[10px] rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
												>
													{$i18n.t('无需认证')}
												</span>
											</div>
											<div class="text-xs text-gray-500 mt-0.5">{preset.description}</div>
											<div class="text-xs text-gray-400 mt-1">
												<code
													class="text-[10px] bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded font-mono break-all"
												>
													{preset.setup_hint}
												</code>
											</div>
										</div>
										<div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-5 h-5 text-gray-400"
											>
												<path
													fill-rule="evenodd"
													d="M3 10a.75.75 0 01.75-.75h10.638l-3.96-4.158a.75.75 0 011.08-1.04l5.25 5.5a.75.75 0 010 1.04l-5.25 5.5a.75.75 0 11-1.08-1.04l3.96-4.158H3.75A.75.75 0 013 10z"
													clip-rule="evenodd"
												/>
											</svg>
										</div>
									</div>
								</button>
							{/each}
						</div>
					</div>

					<!-- Info hint -->
					<div class="text-xs text-gray-400 dark:text-gray-500 text-center pt-2">
						{$i18n.t('仅支持 Streamable HTTP 传输方式')}
					</div>
				</div>
			{/if}
		</div>
	</div>
</Modal>
