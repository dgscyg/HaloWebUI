<script lang="ts">
	import Sortable from 'sortablejs';

	import { createEventDispatcher, getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	import { models } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EllipsisVertical from '$lib/components/icons/EllipsisVertical.svelte';

	export let modelIds = [];

	let sortable = null;
	let modelListElement = null;

	const positionChangeHandler = () => {
		const modelList = Array.from(modelListElement.children).map((child) =>
			child.id.replace('model-item-', '')
		);

		modelIds = modelList;
	};

	$: if (modelIds) {
		init();
	}

	const init = () => {
		if (sortable) {
			sortable.destroy();
		}

		if (modelListElement) {
			sortable = Sortable.create(modelListElement, {
				animation: 150,
				handle: '.item-handle',
				onUpdate: async (event) => {
					positionChangeHandler();
				}
			});
		}
	};
</script>

{#if modelIds.length > 0}
	<div class="flex flex-col gap-0.5" bind:this={modelListElement}>
		{#each modelIds as modelId, modelIdx (modelId)}
			<div
				class="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition group"
				id="model-item-{modelId}"
			>
				<div class="item-handle cursor-grab active:cursor-grabbing text-gray-300 dark:text-gray-600 group-hover:text-gray-400 dark:group-hover:text-gray-500 transition shrink-0">
					<EllipsisVertical className="size-4" />
				</div>

				<Tooltip content={modelId} placement="top-start">
					<div class="text-sm text-gray-700 dark:text-gray-300 truncate">
						{#if $models.find((model) => model.id === modelId)}
							{$models.find((model) => model.id === modelId).name}
						{:else}
							<span class="text-gray-400 dark:text-gray-500 italic">{modelId}</span>
						{/if}
					</div>
				</Tooltip>
			</div>
		{/each}
	</div>
{:else}
	<div class="text-gray-400 dark:text-gray-500 text-xs text-center py-8">
		{$i18n.t('No models found')}
	</div>
{/if}
