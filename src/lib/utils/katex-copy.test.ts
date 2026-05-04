import { describe, expect, it } from 'vitest';

import { getKatexCopyText } from './katex-copy';

describe('getKatexCopyText', () => {
	it('prefers the original markdown source when available', () => {
		expect(
			getKatexCopyText({
				source: String.raw`\[x^2 + y^2 = 1\]`,
				content: 'x^2 + y^2 = 1',
				displayMode: true
			})
		).toBe(String.raw`\[x^2 + y^2 = 1\]`);
	});

	it('falls back to inline delimiters when source is missing', () => {
		expect(
			getKatexCopyText({
				content: 'x^2 + y^2 = 1',
				displayMode: false
			})
		).toBe('$x^2 + y^2 = 1$');
	});

	it('falls back to block delimiters when source is missing', () => {
		expect(
			getKatexCopyText({
				content: String.raw`\frac{a}{b}`,
				displayMode: true
			})
		).toBe('$$\n\\frac{a}{b}\n$$');
	});
});
