<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { functions, user } from '$lib/stores';
	import { updateFunctionById, getFunctions, getFunctionById } from '$lib/apis/functions';

	import FunctionEditor from '$lib/components/admin/Functions/FunctionEditor.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { refreshModels } from '$lib/services/models';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import { WEBUI_VERSION } from '$lib/constants';
	import WorkspaceSubpageHeader from '$lib/components/workspace/shell/WorkspaceSubpageHeader.svelte';
	import { localizeCommonError } from '$lib/utils/common-errors';

	const i18n: Writable<any> = getContext('i18n');
	const formatError = (error: unknown) =>
		localizeCommonError(error, (key, options) => $i18n.t(key, options));

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

		const res = await updateFunctionById(localStorage.token, func.id, {
			id: data.id,
			name: data.name,
			meta: data.meta,
			content: data.content
		}).catch((error) => {
			toast.error(formatError(error));
			return null;
		});

		if (res) {
			toast.success($i18n.t('Function updated successfully'));
			functions.set(await getFunctions(localStorage.token));
			await refreshModels(localStorage.token, { force: true, reason: 'settings-functions' });
			return true;
		}

		return false;
	};

	const onEditorSave = (value: FunctionDraft) => {
		return saveHandler(value);
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			goto('/workspace');
			return;
		}

		const id = $page.url.searchParams.get('id');

		if (id) {
			func = await getFunctionById(localStorage.token, id).catch((error) => {
				toast.error(formatError(error));
				goto('/workspace/functions');
				return null;
			});
		} else {
			goto('/workspace/functions');
		}
	});
</script>

{#if $user?.role === 'admin' && func}
	<div class="space-y-4">
		<WorkspaceSubpageHeader
			backHref="/workspace/functions"
			titleKey="Edit Workspace Function"
			descKey="Revise function behavior, metadata, and code while keeping existing workspace assignments."
		/>

		<FunctionEditor
			edit={true}
			id={func.id}
			name={func.name}
			meta={func.meta}
			content={func.content}
			showBackButton={false}
			onSave={onEditorSave}
		/>
	</div>
{:else if $user?.role === 'admin'}
	<div class="workspace-section flex items-center justify-center h-full">
		<div class="pb-16">
			<Spinner />
		</div>
	</div>
{/if}
