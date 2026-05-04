let katexCopyInitPromise: Promise<void> | null = null;

type KatexCopyTextOptions = {
	source?: string | null;
	content: string;
	displayMode?: boolean;
};

export const getKatexCopyText = ({
	source,
	content,
	displayMode = false
}: KatexCopyTextOptions): string => {
	if (typeof source === 'string' && source !== '') {
		return source;
	}

	if (displayMode) {
		return ['$$', content, '$$'].join('\n');
	}

	return '$' + content + '$';
};

export const ensureKatexCopyTextEnabled = async (): Promise<void> => {
	if (typeof window === 'undefined' || typeof document === 'undefined') {
		return;
	}

	if (!katexCopyInitPromise) {
		katexCopyInitPromise = import('katex/contrib/copy-tex')
			.then(() => undefined)
			.catch((error) => {
				katexCopyInitPromise = null;
				console.error('Failed to enable KaTeX copy support:', error);
			});
	}

	await katexCopyInitPromise;
};
