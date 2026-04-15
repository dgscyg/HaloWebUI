<script>
	import { onDestroy, onMount, tick, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import Markdown from './Markdown.svelte';
	import {
		artifactPreviewTarget,
		chatId,
		mobile,
		settings,
		showArtifacts,
		showControls,
		showOverview
	} from '$lib/stores';
	import FloatingButtons from '../ContentRenderer/FloatingButtons.svelte';
	import { createMessagesList } from '$lib/utils';
	import { getCitationEntries } from '$lib/utils/citations';
	import { resolveChatTransitionMode } from '$lib/utils/lobehub-chat-appearance';

	export let id;
	export let content;
	export let history;
	export let model = null;
	export let sources = null;

	export let save = false;
	export let floatingButtons = true;
	export let actions = [];
	export let streaming = false;
	export let isLastMessage = false;

	export let onSourceClick = () => {};
	export let onTaskClick = () => {};

	export let onAddMessages = () => {};
	export let headings = [];

	let contentContainerElement;
	let floatingButtonsElement;
	let currentTransitionMode = 'none';

	// Long content truncation
	const MAX_CONTENT_HEIGHT = 2000;
	const MESSAGE_OUTLINE_SCROLL_OFFSET = 24;
	let isExpanded = false;
	let needsTruncation = false;
	let resizeObserver;
	let shouldCollapseHistoricalLongResponses = false;

	$: shouldCollapseHistoricalLongResponses =
		!isLastMessage && ($settings?.collapseHistoricalLongResponses ?? true);

	function checkTruncation() {
		if (!contentContainerElement) return;
		if (streaming || isExpanded || !shouldCollapseHistoricalLongResponses) {
			needsTruncation = false;
			return;
		}
		needsTruncation = contentContainerElement.scrollHeight > MAX_CONTENT_HEIGHT;
	}

	$: if (contentContainerElement) {
		isLastMessage;
		shouldCollapseHistoricalLongResponses;

		if (streaming) {
			needsTruncation = false;
		} else {
			// Re-check when streaming ends or truncation rules change
			tick().then(checkTruncation);
		}
	}

	$: currentTransitionMode = resolveChatTransitionMode($settings);

	const highlightHeading = (headingElement) => {
		headingElement.classList.remove('message-outline-anchor-target');
		void headingElement.offsetWidth;
		headingElement.classList.add('message-outline-anchor-target');
		headingElement.addEventListener(
			'animationend',
			() => {
				headingElement.classList.remove('message-outline-anchor-target');
			},
			{ once: true }
		);
	};

	export async function scrollToHeading(headingId) {
		if (needsTruncation && !isExpanded) {
			isExpanded = true;
			await tick();
		}

		await tick();

		const headingElement = contentContainerElement?.querySelector?.(`[id="${headingId}"]`);
		const messagesContainer = document.getElementById('messages-container');

		if (!headingElement || !messagesContainer) {
			return;
		}

		const containerRect = messagesContainer.getBoundingClientRect();
		const headingRect = headingElement.getBoundingClientRect();
		const nextTop =
			messagesContainer.scrollTop +
			(headingRect.top - containerRect.top) -
			MESSAGE_OUTLINE_SCROLL_OFFSET;

		messagesContainer.scrollTo({
			top: Math.max(0, nextTop),
			behavior: 'smooth'
		});

		highlightHeading(headingElement);
	}

	const updateButtonPosition = (event) => {
		const buttonsContainerElement = document.getElementById(`floating-buttons-${id}`);
		if (
			!contentContainerElement?.contains(event.target) &&
			!buttonsContainerElement?.contains(event.target)
		) {
			// Don't dismiss when response is actively showing
			if (floatingButtonsElement?.hasActiveResponse) {
				return;
			}
			closeFloatingButtons();
			return;
		}

		setTimeout(async () => {
			await tick();

			if (!contentContainerElement?.contains(event.target)) return;

			let selection = window.getSelection();

			if (selection.toString().trim().length > 0) {
				const range = selection.getRangeAt(0);
				const rect = range.getBoundingClientRect();

				const parentRect = contentContainerElement.getBoundingClientRect();

				// Adjust based on parent rect
				const top = rect.bottom - parentRect.top;
				const left = rect.left - parentRect.left;

				if (buttonsContainerElement) {
					buttonsContainerElement.style.display = 'block';

					// Calculate space available on the right
					const spaceOnRight = parentRect.width - left;
					let halfScreenWidth = $mobile ? window.innerWidth / 2 : window.innerWidth / 3;

					if (spaceOnRight < halfScreenWidth) {
						const right = parentRect.right - rect.right;
						buttonsContainerElement.style.right = `${right}px`;
						buttonsContainerElement.style.left = 'auto';
					} else {
						buttonsContainerElement.style.left = `${left}px`;
						buttonsContainerElement.style.right = 'auto';
					}

					// Smart vertical positioning: show above selection if not enough space below
					const spaceBelow = parentRect.bottom - rect.bottom;
					const floatingHeight = buttonsContainerElement.offsetHeight || 40;
					const margin = 8;

					if (spaceBelow < floatingHeight + margin) {
						// Not enough space below — position above the selection
						const topAbove = rect.top - parentRect.top - floatingHeight - margin;
						buttonsContainerElement.style.top = `${Math.max(0, topAbove)}px`;
					} else {
						buttonsContainerElement.style.top = `${top + margin}px`;
					}
				}
			} else {
				closeFloatingButtons();
			}
		}, 0);
	};

	const closeFloatingButtons = () => {
		const buttonsContainerElement = document.getElementById(`floating-buttons-${id}`);
		if (buttonsContainerElement) {
			buttonsContainerElement.style.display = 'none';
		}

		if (floatingButtonsElement) {
			// check if closeHandler is defined

			if (typeof floatingButtonsElement?.closeHandler === 'function') {
				// call the closeHandler function
				floatingButtonsElement?.closeHandler();
			}
		}
	};

	const keydownHandler = (e) => {
		if (e.key === 'Escape') {
			closeFloatingButtons();
		}
	};

	onMount(() => {
		if (floatingButtons) {
			contentContainerElement?.addEventListener('mouseup', updateButtonPosition);
			document.addEventListener('mouseup', updateButtonPosition);
			document.addEventListener('keydown', keydownHandler);
		}

		// Observe content height for truncation
		if (contentContainerElement) {
			resizeObserver = new ResizeObserver(checkTruncation);
			resizeObserver.observe(contentContainerElement);
		}
	});

	onDestroy(() => {
		if (floatingButtons) {
			contentContainerElement?.removeEventListener('mouseup', updateButtonPosition);
			document.removeEventListener('mouseup', updateButtonPosition);
			document.removeEventListener('keydown', keydownHandler);
		}
		resizeObserver?.disconnect();
	});
</script>

<div class="relative overflow-visible">
	<div
		bind:this={contentContainerElement}
		class="relative"
		style={needsTruncation && !isExpanded
			? `max-height: ${MAX_CONTENT_HEIGHT}px; overflow: hidden;`
			: ''}
	>
		<Markdown
			bind:headings
			{id}
			content={content || ''}
			{model}
			{save}
			{streaming}
			transitionMode={currentTransitionMode}
				sourceIds={(sources ?? []).reduce((acc, s) => {
					if (!s || typeof s !== 'object') {
						return acc;
					}

					let ids = [];
					getCitationEntries(s).forEach(({ metadata }) => {
						if (model?.info?.meta?.capabilities?.citations == false) {
							ids.push('N/A');
							return;
						}

						const id = metadata?.source ?? 'N/A';

						if (metadata?.name) {
							ids.push(metadata.name);
							return;
						}

						if (
							typeof id === 'string' &&
							(id.startsWith('http://') || id.startsWith('https://'))
						) {
							ids.push(id);
						} else {
							ids.push(s?.source?.name ?? id);
						}
					});

					acc = [...acc, ...ids];

				// remove duplicates
				return acc.filter((item, index) => acc.indexOf(item) === index);
			}, [])}
			{onSourceClick}
			{onTaskClick}
			on:update={(e) => {
				dispatch('update', e.detail);
			}}
			on:code={(e) => {
				const { lang, code } = e.detail;
				const normalizedLang = String(lang ?? '').toLowerCase();
				const isSvgCode =
					normalizedLang === 'svg' || (normalizedLang === 'xml' && code.includes('<svg'));
				const isHtmlArtifact = normalizedLang === 'html';
				const shouldAutoOpenSvgPreview =
					$settings?.svgPreviewAutoOpen ?? ($settings?.detectArtifacts ?? true);

				if (
					!$mobile &&
					$chatId &&
					((($settings?.detectArtifacts ?? true) && isHtmlArtifact) ||
						(shouldAutoOpenSvgPreview && isSvgCode))
				) {
					if (isSvgCode) {
						artifactPreviewTarget.set({ messageId: id, type: 'svg', content: code });
					} else {
						artifactPreviewTarget.set(null);
					}
					showOverview.set(false);
					showArtifacts.set(true);
					showControls.set(true);
				}
			}}
		/>
	</div>
</div>

{#if needsTruncation && !isExpanded}
	<div class="relative -mt-20 pt-20 bg-gradient-to-t from-white dark:from-gray-900 to-transparent">
		<div class="flex justify-center py-2">
			<button
				class="px-4 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-300
					bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
					rounded-full border border-gray-200 dark:border-gray-700
					transition-colors duration-150"
				on:click={() => {
					isExpanded = true;
				}}
			>
				{$i18n.t('Show more')}
			</button>
		</div>
	</div>
{/if}

{#if floatingButtons && model}
	<FloatingButtons
		bind:this={floatingButtonsElement}
		{id}
		model={model?.id}
		messages={createMessagesList(history, id)}
		{actions}
		onAdd={({ modelId, parentId, messages }) => {
			console.log(modelId, parentId, messages);
			onAddMessages({ modelId, parentId, messages });
			closeFloatingButtons();
		}}
	/>
{/if}

<style>
	:global(.message-outline-anchor) {
		scroll-margin-top: 1.5rem;
	}

	:global(.message-outline-anchor-target) {
		animation: message-outline-anchor-flash 900ms ease;
	}

	@keyframes message-outline-anchor-flash {
		0% {
			background-color: rgba(56, 189, 248, 0.18);
			box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.18);
		}

		45% {
			background-color: rgba(56, 189, 248, 0.28);
			box-shadow: 0 0 0 0.45rem rgba(56, 189, 248, 0.12);
		}

		100% {
			background-color: transparent;
			box-shadow: 0 0 0 0 rgba(56, 189, 248, 0);
		}
	}
</style>
