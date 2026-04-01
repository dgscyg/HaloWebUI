<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';

	import type { Model } from '$lib/stores';
	import { mobile } from '$lib/stores';
	import { getImageGenerationModels, getImageUsageConfig, type ImageGenerationModel } from '$lib/apis/images';
	import {
		getUserValvesById as getFunctionUserValvesById,
		getUserValvesSpecById as getFunctionUserValvesSpecById,
		updateUserValvesById as updateFunctionUserValvesById
	} from '$lib/apis/functions';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import HaloSelect from '$lib/components/common/HaloSelect.svelte';
	import PhotoSolid from '$lib/components/icons/PhotoSolid.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import {
		GEMINI_IMAGE_SIZE_OPTIONS,
		IMAGE_ASPECT_RATIO_OPTIONS,
		getFunctionPipeRootId,
		getImageValveProperty,
		getPropertyEnumOptions,
		looksLikeImageValveSpec,
		mapLegacySizeToGeminiParams,
		modelSupportsGeminiImageOptions
	} from '$lib/utils/image-generation';

	const dispatch = createEventDispatcher();

	type ImageGenerationOptions = {
		image_size?: string | null;
		aspect_ratio?: string | null;
		n?: number | null;
	};

	export let currentModel: Model | null = null;
	export let imageGenerationEnabled = false;
	export let imageGenerationOptions: ImageGenerationOptions = {};

	let builtinLoading = false;
	let builtinReady = false;
	let builtinEngine = '';
	let builtinModelMeta: ImageGenerationModel | null = null;
	let builtinRequestKey = '';

	let customLoading = false;
	let customFunctionId = '';
	let customValvesSpec: Record<string, any> | null = null;
	let customValves: Record<string, any> = {};
	let customHasImageFields = false;
	let customLoadedKey = '';

	let panelExpanded = false;
	let expandedInitialized = false;

	const syncInitialExpandState = () => {
		if (expandedInitialized) return;
		panelExpanded = !$mobile;
		expandedInitialized = true;
	};

	$: syncInitialExpandState();

	const applyBuiltinDefaults = (size: string | null, aspectRatio: string | null) => {
		const next: ImageGenerationOptions = { ...imageGenerationOptions };
		let changed = false;

		if ((builtinModelMeta?.supports_image_size ?? false) && !next.image_size && size) {
			next.image_size = size;
			changed = true;
		}
		if (
			((builtinModelMeta?.size_mode ?? '') === 'aspect_ratio' ||
				(builtinModelMeta?.supports_image_size ?? false)) &&
			!next.aspect_ratio &&
			aspectRatio
		) {
			next.aspect_ratio = aspectRatio;
			changed = true;
		}

		if (changed) {
			imageGenerationOptions = next;
		}
	};

	const loadBuiltinContext = async () => {
		const requestKey = imageGenerationEnabled ? 'enabled' : 'disabled';
		if (requestKey === builtinRequestKey) {
			return;
		}
		builtinRequestKey = requestKey;

		if (!imageGenerationEnabled) {
			builtinEngine = '';
			builtinModelMeta = null;
			builtinReady = false;
			return;
		}

		builtinLoading = true;
		try {
			const usageConfig = await getImageUsageConfig(localStorage.token);
			builtinEngine = `${usageConfig?.engine ?? ''}`.toLowerCase();
			if (builtinEngine !== 'gemini') {
				builtinModelMeta = null;
				builtinReady = true;
				return;
			}

			const runtimeModels = await getImageGenerationModels(localStorage.token, {
				context: 'runtime'
			}).catch(() => []);
			const preferredId = `${usageConfig?.defaults?.model ?? ''}`.trim();
			builtinModelMeta =
				(runtimeModels ?? []).find((model) => model.id === preferredId) ??
				(runtimeModels ?? []).find((model) => modelSupportsGeminiImageOptions(model)) ??
				(runtimeModels ?? [])[0] ??
				null;
			builtinReady = true;

			const mappedDefaults = mapLegacySizeToGeminiParams(usageConfig?.defaults?.size ?? '');
			applyBuiltinDefaults(mappedDefaults.imageSize, mappedDefaults.aspectRatio);
		} catch (error) {
			console.error('Failed to load Gemini image context', error);
			builtinModelMeta = null;
			builtinReady = true;
		} finally {
			builtinLoading = false;
		}
	};

	const loadCustomContext = async () => {
		const nextFunctionId =
			currentModel?.pipe && currentModel?.has_user_valves
				? getFunctionPipeRootId(currentModel?.id)
				: '';

		if (nextFunctionId === customLoadedKey) {
			return;
		}
		customLoadedKey = nextFunctionId;

		customFunctionId = nextFunctionId;
		customValvesSpec = null;
		customValves = {};
		customHasImageFields = false;

		if (!nextFunctionId) {
			return;
		}

		customLoading = true;
		try {
			const [nextValves, nextSpec] = await Promise.all([
				getFunctionUserValvesById(localStorage.token, nextFunctionId),
				getFunctionUserValvesSpecById(localStorage.token, nextFunctionId)
			]);

			if (!looksLikeImageValveSpec(nextSpec)) {
				customValvesSpec = nextSpec;
				customValves = nextValves ?? {};
				customHasImageFields = false;
				return;
			}

			customValvesSpec = nextSpec;
			customValves = { ...(nextValves ?? {}) };
			customHasImageFields = true;

			const nextImageSizeProperty = getImageValveProperty(nextSpec, 'image_size');
			const nextAspectRatioProperty = getImageValveProperty(nextSpec, 'aspect_ratio');
			if (customValves.image_size == null && nextImageSizeProperty?.default != null) {
				customValves.image_size = `${nextImageSizeProperty.default}`;
			}
			if (customValves.aspect_ratio == null && nextAspectRatioProperty?.default != null) {
				customValves.aspect_ratio = `${nextAspectRatioProperty.default}`;
			}
		} catch (error) {
			console.error('Failed to load custom image valves', error);
			customHasImageFields = false;
			customValvesSpec = null;
		} finally {
			customLoading = false;
		}
	};

	const saveCustomValves = async (patch: Record<string, any>) => {
		if (!customFunctionId) {
			return;
		}

		const nextValves = {
			...customValves,
			...patch
		};
		customValves = nextValves;

		try {
			const res = await updateFunctionUserValvesById(
				localStorage.token,
				customFunctionId,
				nextValves
			);
			customValves = res ?? nextValves;
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	$: if (imageGenerationEnabled) {
		void loadBuiltinContext();
	} else if (builtinRequestKey !== 'disabled') {
		void loadBuiltinContext();
	}

	$: void loadCustomContext();

	$: showBuiltinPanel =
		imageGenerationEnabled &&
		builtinReady &&
		builtinEngine === 'gemini' &&
		Boolean(builtinModelMeta) &&
		modelSupportsGeminiImageOptions(builtinModelMeta);

	$: showCustomPanel = Boolean(customFunctionId) && customHasImageFields;
	$: showPanel = showCustomPanel || showBuiltinPanel || customLoading || builtinLoading;
	$: panelTitle = showCustomPanel
		? '画图参数'
		: showBuiltinPanel
			? 'Gemini 绘图参数'
			: '图片参数';

	$: builtinImageSizeOptions = GEMINI_IMAGE_SIZE_OPTIONS.map((option) => ({
		value: option.value,
		label: `${option.label} · ${option.pixels}`
	}));
	$: aspectRatioOptions = IMAGE_ASPECT_RATIO_OPTIONS.map((option) => ({
		value: option.value,
		label: option.label
	}));

	$: customImageSizeOptions = getPropertyEnumOptions(
		getImageValveProperty(customValvesSpec, 'image_size'),
		GEMINI_IMAGE_SIZE_OPTIONS.map((option) => ({ value: option.value, label: option.value }))
	);
	$: customAspectRatioOptions = getPropertyEnumOptions(
		getImageValveProperty(customValvesSpec, 'aspect_ratio'),
		IMAGE_ASPECT_RATIO_OPTIONS
	);
</script>

{#if showPanel}
	<div class="px-2.5 pb-1.5 pt-1.5">
		<div class="rounded-2xl border border-gray-200/70 bg-white/85 shadow-sm backdrop-blur-xl dark:border-gray-700/30 dark:bg-white/[0.04]">
			<div class="flex items-center justify-between gap-3 px-3 py-2.5">
				<div class="flex min-w-0 items-center gap-2">
					<div class="flex size-8 shrink-0 items-center justify-center rounded-xl bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200">
						{#if showCustomPanel}
							<Sparkles className="size-4" strokeWidth="2" />
						{:else}
							<PhotoSolid className="size-4" />
						{/if}
					</div>
					<div class="min-w-0">
						<div class="text-sm font-semibold text-gray-900 dark:text-gray-100">{panelTitle}</div>
						<div class="text-[11px] text-gray-500 dark:text-gray-400">
							{#if showCustomPanel}
								当前自定义画图模型的常用参数
							{:else}
								当前会直接传给 Gemini 官方图片接口
							{/if}
						</div>
					</div>
				</div>

				<div class="flex items-center gap-2">
					{#if showCustomPanel}
						<button
							type="button"
							class="rounded-xl border border-gray-200/80 bg-white px-2.5 py-1 text-xs font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700/50 dark:bg-gray-900/70 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:bg-gray-800"
							on:click={() => {
								dispatch('advanced');
							}}
						>
							高级参数
						</button>
					{/if}

					{#if $mobile}
						<button
							type="button"
							class="rounded-xl border border-gray-200/80 bg-white px-2.5 py-1 text-xs font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700/50 dark:bg-gray-900/70 dark:text-gray-300 dark:hover:border-gray-600 dark:hover:bg-gray-800"
							on:click={() => {
								panelExpanded = !panelExpanded;
							}}
						>
							{panelExpanded ? '收起' : '展开'}
						</button>
					{/if}
				</div>
			</div>

			{#if !$mobile || panelExpanded}
				<div class="grid gap-3 border-t border-gray-200/70 px-3 pb-3 pt-3 dark:border-gray-700/30 md:grid-cols-2">
					{#if customLoading || builtinLoading}
						<div class="col-span-full flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
							<Spinner className="size-4" />
							加载图片参数...
						</div>
					{:else if showCustomPanel}
						{#if getImageValveProperty(customValvesSpec, 'image_size')}
							<div class="space-y-1.5">
								<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
									{getImageValveProperty(customValvesSpec, 'image_size')?.title ?? '图片尺寸'}
								</div>
								<HaloSelect
									value={`${customValves?.image_size ?? customImageSizeOptions[0]?.value ?? ''}`}
									options={customImageSizeOptions}
									className="w-full text-xs"
									on:change={(e) => {
										void saveCustomValves({ image_size: e.detail.value });
									}}
								/>
							</div>
						{/if}

						{#if getImageValveProperty(customValvesSpec, 'aspect_ratio')}
							<div class="space-y-1.5">
								<div class="text-xs font-medium text-gray-500 dark:text-gray-400">
									{getImageValveProperty(customValvesSpec, 'aspect_ratio')?.title ?? '图片比例'}
								</div>
								<HaloSelect
									value={`${customValves?.aspect_ratio ?? customAspectRatioOptions[0]?.value ?? ''}`}
									options={customAspectRatioOptions}
									className="w-full text-xs"
									on:change={(e) => {
										void saveCustomValves({ aspect_ratio: e.detail.value });
									}}
								/>
							</div>
						{/if}
					{:else if showBuiltinPanel}
						{#if builtinModelMeta?.supports_image_size}
							<div class="space-y-1.5">
								<div class="text-xs font-medium text-gray-500 dark:text-gray-400">图片尺寸</div>
								<HaloSelect
									value={`${imageGenerationOptions?.image_size ?? builtinImageSizeOptions[1]?.value ?? '1K'}`}
									options={builtinImageSizeOptions}
									className="w-full text-xs"
									on:change={(e) => {
										imageGenerationOptions = {
											...imageGenerationOptions,
											image_size: e.detail.value
										};
									}}
								/>
							</div>
						{/if}

						{#if builtinModelMeta?.size_mode === 'aspect_ratio' || builtinModelMeta?.supports_image_size}
							<div class="space-y-1.5">
								<div class="text-xs font-medium text-gray-500 dark:text-gray-400">图片比例</div>
								<HaloSelect
									value={`${imageGenerationOptions?.aspect_ratio ?? '1:1'}`}
									options={aspectRatioOptions}
									className="w-full text-xs"
									on:change={(e) => {
										imageGenerationOptions = {
											...imageGenerationOptions,
											aspect_ratio: e.detail.value
										};
									}}
								/>
							</div>
						{/if}
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}
