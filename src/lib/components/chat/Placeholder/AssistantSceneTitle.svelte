<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';

	import { getModelChatDisplayName } from '$lib/utils/model-display';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher<{
		clear: void;
	}>();

	export let assistant: any = null;
</script>

{#if assistant}
	<div class="mb-4 flex w-full items-start justify-between gap-4 px-4 @md:max-w-3xl">
		<div class="flex min-w-0 items-center gap-3 text-left">
			<div
				class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gray-50 text-lg dark:bg-gray-800"
			>
				<img
					src={assistant?.info?.meta?.profile_image_url ??
						assistant?.meta?.profile_image_url ??
						'/static/favicon.png'}
					alt={getModelChatDisplayName(assistant)}
					class="h-full w-full object-cover {(assistant?.info?.meta?.profile_image_url ??
					assistant?.meta?.profile_image_url)
						? ''
						: 'dark:invert'}"
					draggable="false"
				/>
			</div>

			<div class="min-w-0">
				<div class="line-clamp-1 text-3xl text-gray-900 dark:text-gray-50">
					{getModelChatDisplayName(assistant)}
				</div>
				{#if (assistant?.info?.meta?.description ?? assistant?.meta?.description ?? '').trim()}
					<div class="mt-1 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">
						{assistant?.info?.meta?.description ?? assistant?.meta?.description}
					</div>
				{/if}
			</div>
		</div>

		<div class="flex shrink-0 items-center gap-2">
			<a
				class="rounded-full px-3 py-1.5 text-sm font-medium transition hover:bg-gray-100 dark:hover:bg-gray-850"
				href={`/workspace/models/edit?id=${encodeURIComponent(assistant.id)}`}
			>
				{$i18n.t('Edit')}
			</a>
			<button
				type="button"
				class="rounded-full p-1.5 transition hover:bg-gray-100 dark:hover:bg-gray-850"
				aria-label={$i18n.t('Close')}
				on:click={() => {
					dispatch('clear');
				}}
			>
				<XMark className="size-4" />
			</button>
		</div>
	</div>
{/if}
