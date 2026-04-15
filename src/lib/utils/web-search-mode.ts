export type WebSearchMode = 'off' | 'halo' | 'native' | 'auto';

export const WEB_SEARCH_MODES: WebSearchMode[] = ['off', 'halo', 'native', 'auto'];

export const WEB_SEARCH_RUNTIME_MODES: Exclude<WebSearchMode, 'off'>[] = ['halo', 'native', 'auto'];

export function isWebSearchMode(value: unknown): value is WebSearchMode {
	return typeof value === 'string' && WEB_SEARCH_MODES.includes(value as WebSearchMode);
}

export function normalizeWebSearchMode(
	value: unknown,
	fallback: WebSearchMode = 'off'
): WebSearchMode {
	if (value === true || value === 'always') {
		return 'halo';
	}

	if (typeof value === 'string') {
		const normalized = value.trim().toLowerCase();
		if (isWebSearchMode(normalized)) {
			return normalized;
		}
	}

	return fallback;
}

export function getPreferredWebSearchMode(
	settingsValue: { webSearchMode?: unknown; webSearch?: unknown } | null | undefined,
	fallback: WebSearchMode = 'off'
): WebSearchMode {
	if (
		settingsValue &&
		settingsValue.webSearchMode !== undefined &&
		settingsValue.webSearchMode !== null
	) {
		return normalizeWebSearchMode(settingsValue.webSearchMode, fallback);
	}

	if (settingsValue?.webSearch === 'always' || settingsValue?.webSearch === true) {
		return 'halo';
	}

	return fallback;
}

export function isWebSearchEnabled(mode: WebSearchMode | null | undefined): boolean {
	return normalizeWebSearchMode(mode, 'off') !== 'off';
}

export function getWebSearchModeLabel(mode: WebSearchMode | null | undefined): string {
	switch (normalizeWebSearchMode(mode, 'off')) {
		case 'halo':
			return 'HaloWebUI';
		case 'native':
			return '模型原生联网';
		case 'auto':
			return '自动';
		default:
			return '关闭';
	}
}
