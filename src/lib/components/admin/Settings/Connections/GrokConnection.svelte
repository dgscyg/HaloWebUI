<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import Cog6 from '$lib/components/icons/Cog6.svelte';
	import LetterAvatar from '$lib/components/common/LetterAvatar.svelte';
	import ModelIcon from '$lib/components/common/ModelIcon.svelte';
	import AddConnectionModal from '$lib/components/AddConnectionModal.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

	export let onDelete = () => {};
	export let onSubmit = () => {};

	export let url = '';
	export let key = '';
	export let config = {};

	let showConfigModal = false;
	let showDeleteConfirmDialog = false;

	$: isEnabled = config?.enable ?? true;
	$: displayName = config?.remark || url;
	$: tags = config?.tags ?? [];
</script>

<ConfirmDialog
	bind:show={showDeleteConfirmDialog}
	on:confirm={() => {
		onDelete();
	}}
/>

<AddConnectionModal
	edit
	grok
	bind:show={showConfigModal}
	connection={{
		url,
		key,
		config
	}}
	onDelete={() => {
		showDeleteConfirmDialog = true;
	}}
	onSubmit={async (connection) => {
		url = connection.url;
		key = connection.key;
		config = connection.config;
		await onSubmit(connection);
	}}
/>

<button
	type="button"
	class="w-full bg-white dark:bg-gray-900 rounded-lg px-4 py-3 border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition cursor-pointer text-left {!isEnabled
		? 'opacity-60'
		: ''}"
	on:click={() => {
		showConfigModal = true;
	}}
>
	<div class="flex items-center justify-between gap-3">
		<div class="flex items-center gap-3 flex-1 min-w-0">
			{#if config?.icon}
				<ModelIcon src={config.icon} alt="avatar" className="rounded-xl size-8 shrink-0" />
			{:else}
				<LetterAvatar name={displayName} size="size-8" />
			{/if}
			<div class="flex-1 min-w-0">
				<div class="flex items-center gap-2 flex-wrap">
					<div class="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
						{displayName}
					</div>
					{#if !isEnabled}
						<span
							class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 rounded"
						>
							{$i18n.t('Disabled')}
						</span>
					{/if}
					{#each tags as tag}
						<span
							class="text-xs px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded"
						>
							{tag.name}
						</span>
					{/each}
				</div>
				{#if config?.remark && url}
					<div class="text-xs text-gray-400 dark:text-gray-500 truncate mt-0.5">
						{url}
					</div>
				{/if}
			</div>
		</div>
		<div class="flex-shrink-0">
			<Cog6 className="size-4 text-gray-400 dark:text-gray-500" />
		</div>
	</div>
</button>
