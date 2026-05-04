<script lang="ts">
	import DOMPurify from 'dompurify';

	import { onMount, getContext, createEventDispatcher, onDestroy, tick } from 'svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { fade } from 'svelte/transition';
	import { flyAndScale } from '$lib/utils/transitions';
	import { marked } from 'marked';
	import { lockBodyScroll, unlockBodyScroll } from '$lib/utils/body-scroll-lock';

	export let title = '';
	export let message = '';

	export let cancelLabel = $i18n.t('Cancel');
	export let confirmLabel = $i18n.t('Confirm');

	export let onConfirm = () => {};

	export let cancelDisabled = false;
	export let confirmDisabled = false;
	export let closeOnConfirm = true;

	export let cancelButtonClass =
		'text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white font-medium w-full py-2 rounded-xl transition';
	export let confirmButtonClass =
		'text-sm bg-gray-900 hover:bg-gray-850 text-gray-100 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-800 font-medium w-full py-2 rounded-xl transition';

	export let input = false;
	export let inputPlaceholder = '';
	export let inputValue = '';

	export let show = false;

	$: if (show) {
		init();
	}

	let modalElement = null;
	let mounted = false;
	let isAttached = false;

	const init = () => {
		inputValue = '';
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			if (cancelDisabled) return;
			show = false;
			dispatch('cancel');
		}

		if (event.key === 'Enter') {
			if (confirmDisabled) return;
			confirmHandler();
		}
	};

	const confirmHandler = async () => {
		if (confirmDisabled) return;

		if (closeOnConfirm) {
			show = false;
			await tick();
		}

		try {
			await onConfirm();
			dispatch('confirm', inputValue);

			if (!closeOnConfirm) {
				show = false;
			}
		} catch {
			// Keep the dialog open on failure when `closeOnConfirm` is false.
		}
	};

	onMount(() => {
		mounted = true;
	});

	const attachDialog = () => {
		if (!modalElement || isAttached) return;

		document.body.appendChild(modalElement);
		window.addEventListener('keydown', handleKeyDown);
		lockBodyScroll();
		isAttached = true;
	};

	const detachDialog = () => {
		if (!modalElement || !isAttached) return;

		window.removeEventListener('keydown', handleKeyDown);

		if (document.body.contains(modalElement)) {
			document.body.removeChild(modalElement);
		}

		unlockBodyScroll();
		isAttached = false;
	};

	$: if (mounted) {
		if (show && modalElement) {
			attachDialog();
		} else if (modalElement) {
			detachDialog();
		}
	}

	onDestroy(() => {
		show = false;
		detachDialog();
	});
</script>

{#if show}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		bind:this={modalElement}
		class=" fixed top-0 right-0 left-0 bottom-0 bg-black/60 w-full h-screen max-h-[100dvh] flex justify-center z-99999999 overflow-hidden overscroll-contain"
		in:fade={{ duration: 10 }}
		on:mousedown={() => {
			if (cancelDisabled) return;
			show = false;
			dispatch('cancel');
		}}
	>
		<div
			class=" m-auto max-w-full w-[32rem] mx-2 bg-white/95 dark:bg-gray-950/95 backdrop-blur-sm rounded-2xl max-h-[100dvh] shadow-3xl border border-white dark:border-gray-900"
			in:flyAndScale
			on:mousedown={(e) => {
				e.stopPropagation();
			}}
		>
			<div class="px-[1.75rem] py-6 flex flex-col">
				<div class=" text-lg font-medium dark:text-gray-200 mb-2.5">
					{#if title !== ''}
						{title}
					{:else}
						{$i18n.t('Confirm your action')}
					{/if}
				</div>

				<slot>
					<div class=" text-sm text-gray-500 flex-1">
						{#if message !== ''}
							{@const html = DOMPurify.sanitize(marked.parse(message))}
							{@html html}
						{:else}
							{$i18n.t('This action cannot be undone. Do you wish to continue?')}
						{/if}

						{#if input}
							<textarea
								bind:value={inputValue}
								placeholder={inputPlaceholder ? inputPlaceholder : $i18n.t('Enter your message')}
								class="w-full mt-2 rounded-lg px-4 py-2 text-sm dark:text-gray-300 dark:bg-gray-900 outline-hidden resize-none"
								rows="3"
								required
							/>
						{/if}
					</div>
				</slot>

				<div class="mt-6 flex justify-between gap-1.5">
					<button
						class={`${cancelButtonClass} ${cancelDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
						on:click={() => {
							if (cancelDisabled) return;
							show = false;
							dispatch('cancel');
						}}
						type="button"
						disabled={cancelDisabled}
					>
						{cancelLabel}
					</button>
					<button
						class={`${confirmButtonClass} ${confirmDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
						on:click={() => {
							confirmHandler();
						}}
						type="button"
						disabled={confirmDisabled}
					>
						{confirmLabel}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
