<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { marked } from 'marked';

	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { blur, fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	import { config, user, models as _models, temporaryChatEnabled, settings, type Model } from '$lib/stores';
	import { sanitizeResponseContent, extractCurlyBraceWords } from '$lib/utils';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import Suggestions from './Suggestions.svelte';
	import ModelIcon from '$lib/components/common/ModelIcon.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { getModelChatDisplayName } from '$lib/utils/model-display';
	import type { WebSearchMode } from '$lib/utils/web-search-mode';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import MessageInput from './MessageInput.svelte';

	const i18n = getContext('i18n');

	export let transparentBackground = false;

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;

	export let atSelectedModel: Model | undefined;
	export let selectedModels: [''];

	export let history;

	export let prompt = '';
	export let files = [];

	export let selectedToolIds = [];
	export let imageGenerationEnabled = false;
	export let imageGenerationOptions = {};
	export let codeInterpreterEnabled = false;
	export let webSearchMode: WebSearchMode = 'off';

	export let reasoningEffort: string | null = null;
	export let maxThinkingTokens: number | null = null;

	export let toolServers = [];

	let models = [];

	const selectSuggestionPrompt = async (p) => {
		let text = p;

		if (p.includes('{{CLIPBOARD}}')) {
			const clipboardText = await navigator.clipboard.readText().catch((err) => {
				toast.error($i18n.t('Failed to read clipboard contents'));
				return '{{CLIPBOARD}}';
			});

			text = p.replaceAll('{{CLIPBOARD}}', clipboardText);

			console.log('Clipboard text:', clipboardText, text);
		}

		prompt = text;

		console.log(prompt);
		await tick();

		const chatInputContainerElement = document.getElementById('chat-input-container');
		const chatInputElement = document.getElementById('chat-input');

		if (chatInputContainerElement) {
			chatInputContainerElement.scrollTop = chatInputContainerElement.scrollHeight;
		}

		await tick();
		if (chatInputElement) {
			chatInputElement.focus();
			chatInputElement.dispatchEvent(new Event('input'));
		}

		await tick();

		if (!($settings?.insertSuggestionPrompt ?? false)) {
			dispatch('submit', text);
		}
	};

	let selectedModelIdx = 0;

	$: if (selectedModels.length > 0) {
		selectedModelIdx = models.length - 1;
	}

	$: models = selectedModels.map((id) => $_models.find((m) => m.id === id));
	$: promptSuggestionsEnabled = $config?.features?.enable_prompt_suggestions ?? true;

	onMount(() => {});
</script>

<div class="m-auto w-full max-w-6xl px-4 @2xl:px-20 translate-y-2 py-16 text-center">
	{#if $temporaryChatEnabled}
		<Tooltip
			content={$i18n.t('This chat won’t appear in history and your messages will not be saved.')}
			className="w-full flex justify-center mb-0.5"
			placement="top"
		>
			<div class="flex items-center gap-2 text-gray-500 font-medium text-lg my-2 w-fit">
				<EyeSlash strokeWidth="2.5" className="size-5" />{$i18n.t('Temporary Chat')}
			</div>
		</Tooltip>
	{/if}

	<div class="w-full text-gray-800 dark:text-gray-100 text-center flex items-center font-primary">
		<div class="w-full flex flex-col justify-center items-center">
			<!-- Logo/Avatar 区域 - 居中显示，更大尺寸 -->
			<div class="flex justify-center mb-4" in:fade={{ duration: 100 }}>
				<div class="flex -space-x-4">
					{#each models as model, modelIdx}
						<Tooltip
							content={(models[modelIdx]?.info?.meta?.tags ?? [])
								.map((tag) => tag.name.toUpperCase())
								.join(', ')}
							placement="top"
						>
							<button
								on:click={() => {
									selectedModelIdx = modelIdx;
								}}
							>
								<ModelIcon
									src={model?.info?.meta?.profile_image_url ??
										model?.meta?.profile_image_url ??
										($i18n.language === 'dg-DG'
											? `/doge.png`
											: `${WEBUI_BASE_URL}/static/favicon.png`)}
									className="size-14 @sm:size-16 rounded-2xl border-2 border-white dark:border-gray-800 shadow-lg"
									alt="logo"
								/>
							</button>
						</Tooltip>
					{/each}
				</div>
			</div>

			<!-- 模型名称/问候语 - 字体适中 -->
			<div class="text-xl @sm:text-2xl font-medium line-clamp-1 px-4" in:fade={{ duration: 100 }}>
				{#if models[selectedModelIdx]?.name}
					{getModelChatDisplayName(models[selectedModelIdx])}
				{:else}
					{$i18n.t('Hello, {{name}}', { name: $user?.name })}
				{/if}
			</div>

			<!-- 模型描述 -->
			<div class="flex mt-2 mb-4">
				<div in:fade={{ duration: 100, delay: 50 }}>
					{#if models[selectedModelIdx]?.info?.meta?.description ?? null}
						<Tooltip
							className=" w-fit"
							content={marked.parse(
								sanitizeResponseContent(models[selectedModelIdx]?.info?.meta?.description ?? '')
							)}
							placement="top"
						>
							<div
								class="mt-0.5 px-3 text-sm font-normal text-gray-500 dark:text-gray-400 line-clamp-2 max-w-xl markdown"
							>
								{@html marked.parse(
									sanitizeResponseContent(models[selectedModelIdx]?.info?.meta?.description)
								)}
							</div>
						</Tooltip>

						{#if models[selectedModelIdx]?.info?.meta?.user}
							<div class="mt-0.5 text-sm font-normal text-gray-400 dark:text-gray-500">
								By
								{#if models[selectedModelIdx]?.info?.meta?.user.community}
									<a
										href="https://openwebui.com/m/{models[selectedModelIdx]?.info?.meta?.user
											.username}"
										>{models[selectedModelIdx]?.info?.meta?.user.name
											? models[selectedModelIdx]?.info?.meta?.user.name
											: `@${models[selectedModelIdx]?.info?.meta?.user.username}`}</a
									>
								{:else}
									{models[selectedModelIdx]?.info?.meta?.user.name}
								{/if}
							</div>
						{/if}
					{/if}
				</div>
			</div>

			<div
				class="text-base font-normal @md:max-w-3xl w-full pt-2 pb-3 {atSelectedModel ? 'mt-2' : ''}"
			>
				<MessageInput
					{history}
					{selectedModels}
					bind:files
					bind:prompt
					bind:autoScroll
					bind:selectedToolIds
					bind:imageGenerationEnabled
					bind:imageGenerationOptions
					bind:codeInterpreterEnabled
					bind:webSearchMode
					bind:atSelectedModel
					bind:reasoningEffort
					bind:maxThinkingTokens
					{toolServers}
					{transparentBackground}
					{stopResponse}
					{createMessagePair}
					placeholder={$i18n.t('How can I help you today?')}
					on:upload={(e) => {
						dispatch('upload', e.detail);
					}}
					on:submit={(e) => {
						dispatch('submit', e.detail);
					}}
				/>
			</div>
		</div>
	</div>
	{#if promptSuggestionsEnabled}
		<div class="mx-auto max-w-3xl font-primary" in:fade={{ duration: 200, delay: 200 }}>
			<div class="mx-4">
				<Suggestions
					suggestionPrompts={atSelectedModel?.info?.meta?.suggestion_prompts ??
						models[selectedModelIdx]?.info?.meta?.suggestion_prompts ??
						$config?.default_prompt_suggestions ??
						[]}
					inputValue={prompt}
					on:select={(e) => {
						selectSuggestionPrompt(e.detail);
					}}
				/>
			</div>
		</div>
	{/if}
</div>
