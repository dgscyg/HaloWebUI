export type GeminiImageSizeOption = {
	value: string;
	label: string;
	pixels: string;
};

export type AspectRatioOption = {
	value: string;
	label: string;
};

export type NativeResolutionOption = {
	value: string;
	label: string;
};

export const GEMINI_IMAGE_SIZE_OPTIONS: GeminiImageSizeOption[] = [
	{ value: '512', label: '512', pixels: '512x512' },
	{ value: '1K', label: '1K', pixels: '1024x1024' },
	{ value: '2K', label: '2K', pixels: '2048x2048' },
	{ value: '4K', label: '4K', pixels: '4096x4096' }
];

export const IMAGE_ASPECT_RATIO_OPTIONS: AspectRatioOption[] = [
	{ value: '1:1', label: '1:1' },
	{ value: '2:3', label: '2:3' },
	{ value: '3:2', label: '3:2' },
	{ value: '3:4', label: '3:4' },
	{ value: '4:3', label: '4:3' },
	{ value: '4:5', label: '4:5' },
	{ value: '5:4', label: '5:4' },
	{ value: '9:16', label: '9:16' },
	{ value: '16:9', label: '16:9' },
	{ value: '21:9', label: '21:9' }
];

export const GROK_IMAGE_ASPECT_RATIO_OPTIONS: AspectRatioOption[] = [
	{ value: '1:1', label: '1:1' },
	{ value: '16:9', label: '16:9' },
	{ value: '9:16', label: '9:16' },
	{ value: '4:3', label: '4:3' },
	{ value: '3:4', label: '3:4' },
	{ value: '3:2', label: '3:2' },
	{ value: '2:3', label: '2:3' },
	{ value: '2:1', label: '2:1' },
	{ value: '1:2', label: '1:2' },
	{ value: '19.5:9', label: '19.5:9' },
	{ value: '9:19.5', label: '9:19.5' },
	{ value: '20:9', label: '20:9' },
	{ value: '9:20', label: '9:20' },
	{ value: 'auto', label: 'auto' }
];

export const GROK_IMAGE_RESOLUTION_OPTIONS: NativeResolutionOption[] = [
	{ value: '1k', label: '1K' },
	{ value: '2k', label: '2K' }
];

const LEGACY_SIZE_TO_GEMINI_IMAGE_SIZE: Record<string, string> = {
	'512x512': '512',
	'1024x1024': '1K',
	'2048x2048': '2K',
	'4096x4096': '4K'
};

const LEGACY_SIZE_TO_ASPECT_RATIO: Record<string, string> = {
	'512x512': '1:1',
	'1024x1024': '1:1',
	'1024x1536': '2:3',
	'1536x1024': '3:2'
};

export const normalizeGeminiImageSize = (value: unknown): string | null => {
	const normalized = `${value ?? ''}`.trim().toUpperCase();
	return GEMINI_IMAGE_SIZE_OPTIONS.some((option) => option.value === normalized) ? normalized : null;
};

export const normalizeAspectRatio = (value: unknown): string | null => {
	const normalized = `${value ?? ''}`.trim();
	return IMAGE_ASPECT_RATIO_OPTIONS.some((option) => option.value === normalized) ? normalized : null;
};

export const normalizeGrokAspectRatio = (value: unknown): string | null => {
	const normalized = `${value ?? ''}`.trim();
	return GROK_IMAGE_ASPECT_RATIO_OPTIONS.some((option) => option.value === normalized)
		? normalized
		: null;
};

export const normalizeGrokResolution = (value: unknown): string | null => {
	const normalized = `${value ?? ''}`.trim().toLowerCase();
	return GROK_IMAGE_RESOLUTION_OPTIONS.some((option) => option.value === normalized)
		? normalized
		: null;
};

export const mapLegacySizeToGeminiParams = (size: unknown): {
	imageSize: string | null;
	aspectRatio: string | null;
} => {
	const normalized = `${size ?? ''}`.trim().toLowerCase();
	if (!normalized) {
		return { imageSize: null, aspectRatio: null };
	}

	const imageSize = LEGACY_SIZE_TO_GEMINI_IMAGE_SIZE[normalized] ?? null;
	const presetAspectRatio = LEGACY_SIZE_TO_ASPECT_RATIO[normalized];
	if (presetAspectRatio) {
		return { imageSize, aspectRatio: presetAspectRatio };
	}

	const match = normalized.match(/^(\d+)x(\d+)$/);
	if (!match) {
		return { imageSize, aspectRatio: null };
	}

	const width = Number(match[1]);
	const height = Number(match[2]);
	if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
		return { imageSize, aspectRatio: null };
	}

	const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
	const divisor = gcd(width, height);
	return {
		imageSize,
		aspectRatio: divisor > 0 ? `${width / divisor}:${height / divisor}` : null
	};
};

export const getFunctionPipeRootId = (modelId: unknown): string => {
	const raw = `${modelId ?? ''}`.trim();
	if (!raw) return '';
	return raw.includes('.') ? raw.split('.', 1)[0] : raw;
};

export const looksLikeImageValveSpec = (schema: any): boolean => {
	const properties = schema?.properties ?? {};
	return Boolean(properties?.image_size || properties?.aspect_ratio || properties?.resolution);
};

export const getImageValveProperty = (
	schema: any,
	key: 'image_size' | 'aspect_ratio' | 'resolution'
) =>
	schema?.properties?.[key] ?? null;

export const getPropertyEnumOptions = (
	property: any,
	fallback: Array<{ value: string; label: string }>
) => {
	const enumValues = Array.isArray(property?.enum) ? property.enum : [];
	if (enumValues.length > 0) {
		return enumValues.map((value: unknown) => ({
			value: `${value ?? ''}`,
			label: `${value ?? ''}`
		}));
	}

	return fallback;
};

export const modelSupportsNativeImageOptions = (model: any): boolean =>
	Boolean(
		model &&
			((model?.supports_image_size ?? false) ||
				(model?.supports_resolution ?? false) ||
				model?.size_mode === 'aspect_ratio' ||
				model?.generation_mode === 'gemini_generate_content_image' ||
				model?.generation_mode === 'xai_images')
	);

export const modelSupportsGeminiImageOptions = (model: any): boolean =>
	Boolean(
		model &&
			((model?.supports_image_size ?? false) ||
				model?.generation_mode === 'gemini_generate_content_image')
	);
