<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { lockBodyScroll, unlockBodyScroll } from '$lib/utils/body-scroll-lock';

	export let x;
	export let y;

	let popupElement = null;

	onMount(() => {
		document.body.appendChild(popupElement);
		lockBodyScroll();
	});

	onDestroy(() => {
		if (document.body.contains(popupElement)) {
			document.body.removeChild(popupElement);
		}
		unlockBodyScroll();
	});
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->

<div
	bind:this={popupElement}
	class="fixed top-0 left-0 w-screen h-[100dvh] z-50 touch-none pointer-events-none"
>
	<div class=" absolute text-white z-99999" style="top: {y + 10}px; left: {x + 10}px;">
		<slot></slot>
	</div>
</div>
