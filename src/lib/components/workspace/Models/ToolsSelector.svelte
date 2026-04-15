<script lang="ts">
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import { getContext, onMount } from 'svelte';

	export let tools = [];

	let _tools = {};

	export let selectedToolIds = [];

	const i18n = getContext('i18n');

	onMount(() => {
		_tools = tools.reduce((acc, tool) => {
			acc[tool.id] = {
				...tool,
				selected: selectedToolIds.includes(tool.id)
			};

			return acc;
		}, {});
	});
</script>

<div>
	<div class="text-sm font-medium mb-2">{$i18n.t('Tools')}</div>

	<div class="text-xs text-gray-500 dark:text-gray-400 mb-3">
		{$i18n.t('To select toolkits here, add them to the "Tools" workspace first.')}
	</div>

	{#if tools.length > 0}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
			{#each Object.keys(_tools) as tool}
				<label
					class="flex items-center gap-2.5 py-1.5 px-2 rounded-lg hover:bg-gray-50/50 dark:hover:bg-gray-800/30 cursor-pointer transition-colors"
				>
					<Checkbox
						state={_tools[tool].selected ? 'checked' : 'unchecked'}
						on:change={(e) => {
							_tools[tool].selected = e.detail === 'checked';
							selectedToolIds = Object.keys(_tools).filter((t) => _tools[t].selected);
						}}
					/>
					<span class="text-sm capitalize font-medium">{_tools[tool].name}</span>
				</label>
			{/each}
		</div>
	{/if}
</div>
