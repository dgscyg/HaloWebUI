<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import { goto } from '$app/navigation';

	import { functions, user } from '$lib/stores';
	import { createNewFunction, getFunctions } from '$lib/apis/functions';
	import FunctionEditor from '$lib/components/admin/Functions/FunctionEditor.svelte';
	import { refreshModels } from '$lib/services/models';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import { WEBUI_VERSION } from '$lib/constants';
	import WorkspaceSubpageHeader from '$lib/components/workspace/shell/WorkspaceSubpageHeader.svelte';
	import { localizeCommonError } from '$lib/utils/common-errors';

	const i18n: Writable<any> = getContext('i18n');
	const formatError = (error: unknown) =>
		localizeCommonError(error, (key, options) => $i18n.t(key, options));

	let mounted = false;
	let clone = false;
	let func: any = null;

	type FunctionDraft = {
		id: string;
		name: string;
		meta: any;
		content: string;
	};

	const saveHandler = async (data: FunctionDraft) => {
		const manifest: any = extractFrontmatter(data.content);
		if (compareVersion(manifest?.required_open_webui_version ?? '0.0.0', WEBUI_VERSION)) {
			toast.error(
				$i18n.t(
					'Open WebUI version (v{{OPEN_WEBUI_VERSION}}) is lower than required version (v{{REQUIRED_VERSION}})',
					{
						OPEN_WEBUI_VERSION: WEBUI_VERSION,
						REQUIRED_VERSION: manifest?.required_open_webui_version ?? '0.0.0'
					}
				)
			);
			return false;
		}

		const res = await createNewFunction(localStorage.token, {
			id: data.id,
			name: data.name,
			meta: data.meta,
			content: data.content
		}).catch((error) => {
			toast.error(formatError(error));
			return null;
		});

		if (res) {
			toast.success($i18n.t('Function created successfully'));
			functions.set(await getFunctions(localStorage.token));
			await refreshModels(localStorage.token, { force: true, reason: 'settings-functions' });

			await goto('/workspace/functions');
			return true;
		}

		return false;
	};

	const onEditorSave = (value: FunctionDraft) => {
		return saveHandler(value);
	};

	onMount(() => {
		if ($user?.role !== 'admin') {
			goto('/workspace');
			return;
		}

		window.addEventListener('message', async (event: MessageEvent) => {
			if (
				!['https://openwebui.com', 'https://www.openwebui.com', 'http://localhost:9999'].includes(
					event.origin
				)
			)
				return;

			func = JSON.parse(event.data);
		});

		if (window.opener ?? false) {
			window.opener.postMessage('loaded', '*');
		}

		if (sessionStorage.function) {
			func = JSON.parse(sessionStorage.function);
			sessionStorage.removeItem('function');
			clone = true;
		}

		mounted = true;
	});
</script>

{#if $user?.role === 'admin' && mounted}
	<div class="space-y-4">
		<WorkspaceSubpageHeader
			backHref="/workspace/functions"
			titleKey="Create Workspace Function"
			descKey="Add a new function, filter, or action for admin-managed workspace automation."
		/>

		{#key func?.content}
			<FunctionEditor
				id={func?.id ?? ''}
				name={func?.name ?? ''}
				meta={func?.meta ?? { description: '' }}
				content={func?.content ?? ''}
				{clone}
				showBackButton={false}
				onSave={onEditorSave}
			/>
		{/key}
	</div>
{/if}
