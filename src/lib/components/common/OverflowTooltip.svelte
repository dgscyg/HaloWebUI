<script lang="ts">
	import { onDestroy, onMount, tick } from 'svelte';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let content = '';
	export let className = '';
	export let textClassName = '';
	export let placement = 'top-start';
	export let theme = '';
	export let touch = true;
	export let allowHTML = false;
	export let tippyOptions = {
		delay: [180, 0],
		duration: [140, 90],
		maxWidth: 360
	};

	let textEl: HTMLElement | null = null;
	let resizeObserver: ResizeObserver | null = null;
	let isOverflowing = false;

	const isElementNode = (node: unknown): node is Element =>
		typeof Element !== 'undefined' && node instanceof Element;

	const measureOverflow = () => {
		if (!isElementNode(textEl)) {
			isOverflowing = false;
			return;
		}

		isOverflowing =
			textEl.scrollWidth - textEl.clientWidth > 1 || textEl.scrollHeight - textEl.clientHeight > 1;
	};

	const observeTextEl = () => {
		if (!resizeObserver || !isElementNode(textEl)) return;
		resizeObserver.disconnect();
		resizeObserver.observe(textEl);
	};

	onMount(async () => {
		if (typeof ResizeObserver !== 'undefined') {
			resizeObserver = new ResizeObserver(() => {
				measureOverflow();
			});
			observeTextEl();
		}

		await tick();
		measureOverflow();
	});

	onDestroy(() => {
		resizeObserver?.disconnect();
	});

	$: if (textEl) {
		content;
		textClassName;
		className;
		tick().then(() => {
			observeTextEl();
			measureOverflow();
		});
	}

	$: tooltipContent = isOverflowing ? content : '';
</script>

<Tooltip
	content={tooltipContent}
	{placement}
	{theme}
	{touch}
	{allowHTML}
	{tippyOptions}
	{className}
>
	<span bind:this={textEl} class={textClassName} title={isOverflowing ? content : undefined}>
		<slot>{content}</slot>
	</span>
</Tooltip>
