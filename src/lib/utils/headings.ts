import { marked, type Token } from 'marked';

import { promoteSvgMarkupTokens } from '../components/chat/Messages/Markdown/svgMarkupTokens';

export interface HeadingItem {
	depth: number;
	text: string;
	id: string;
}

type HeadingPath = number[];

type RenderableToken = Token & {
	depth?: number;
	text?: string;
	lang?: string;
	tokens?: Token[];
	items?: Array<{ tokens?: Token[] }>;
};

const CODE_BLOCK_DEPTH = 2;
const CODE_BLOCK_FALLBACK_LABEL = 'Code Block';

const CODE_BLOCK_LANGUAGE_LABELS: Record<string, string> = {
	sql: 'SQL',
	docker: 'Docker',
	dockerfile: 'Dockerfile',
	powershell: 'PowerShell',
	ps1: 'PowerShell',
	yaml: 'YAML',
	yml: 'YAML',
	xml: 'XML',
	json: 'JSON',
	html: 'HTML',
	css: 'CSS',
	js: 'JavaScript',
	javascript: 'JavaScript',
	ts: 'TypeScript',
	typescript: 'TypeScript',
	jsx: 'JSX',
	tsx: 'TSX',
	bash: 'Bash',
	sh: 'Shell',
	shell: 'Shell',
	python: 'Python',
	py: 'Python'
};

const collapseWhitespace = (value: string) => value.replace(/\s+/g, ' ').trim();

export const getHeadingAnchorId = (messageId: string, tokenPath: HeadingPath) =>
	`heading-${messageId}-${tokenPath.join('-')}`;

function extractInlineText(tokens: any[] = []): string {
	return collapseWhitespace(
		tokens
			.map((token) => {
				if (typeof token?.text === 'string' && token.text.trim() !== '') {
					return token.text;
				}

				if (Array.isArray(token?.tokens) && token.tokens.length > 0) {
					return extractInlineText(token.tokens);
				}

				if (typeof token?.raw === 'string') {
					return token.raw;
				}

				return '';
			})
			.join('')
	);
}

function formatCodeBlockLabel(language: string): string {
	const normalizedLanguage = collapseWhitespace(language).toLowerCase();

	if (!normalizedLanguage) {
		return CODE_BLOCK_FALLBACK_LABEL;
	}

	const knownLabel = CODE_BLOCK_LANGUAGE_LABELS[normalizedLanguage];
	if (knownLabel) {
		return knownLabel;
	}

	return normalizedLanguage
		.split(/[^a-z0-9]+/i)
		.filter(Boolean)
		.map((segment) => {
			if (segment.length <= 3) {
				return segment.toUpperCase();
			}

			return segment.charAt(0).toUpperCase() + segment.slice(1);
		})
		.join(' ');
}

function getCodeBlockLabel(token: RenderableToken): string {
	return formatCodeBlockLabel(token.lang ?? '');
}

function visitRenderableTokens(
	tokens: Token[] = [],
	visitor: (token: RenderableToken, tokenPath: HeadingPath) => void,
	pathPrefix: HeadingPath = []
) {
	const normalizedTokens = promoteSvgMarkupTokens(tokens);

	for (let tokenIdx = 0; tokenIdx < normalizedTokens.length; tokenIdx += 1) {
		const token = normalizedTokens[tokenIdx] as RenderableToken;
		const tokenPath = [...pathPrefix, tokenIdx];

		visitor(token, tokenPath);

		if (token.type === 'blockquote' && Array.isArray(token.tokens)) {
			visitRenderableTokens(token.tokens, visitor, tokenPath);
			continue;
		}

		if (token.type === 'list' && Array.isArray(token.items)) {
			token.items.forEach((item, itemIdx) => {
				if (Array.isArray(item?.tokens)) {
					visitRenderableTokens(item.tokens, visitor, [...tokenPath, itemIdx]);
				}
			});
			continue;
		}

		if (token.type === 'details' && typeof token.text === 'string' && token.text.trim() !== '') {
			visitRenderableTokens(marked.lexer(token.text), visitor, tokenPath);
		}
	}
}

export function extractHeadings(tokens: Token[] = [], messageId: string): HeadingItem[] {
	const headings: HeadingItem[] = [];

	visitRenderableTokens(tokens, (token, tokenPath) => {
		if (token.type === 'heading') {
			const depth = token.depth ?? 0;

			if (depth < 1 || depth > 6) {
				return;
			}

			const text = collapseWhitespace(extractInlineText(token.tokens ?? []) || token.text || '');

			if (!text) {
				return;
			}

			headings.push({
				depth,
				text,
				id: getHeadingAnchorId(messageId, tokenPath)
			});
			return;
		}

		if (token.type === 'code') {
			headings.push({
				depth: CODE_BLOCK_DEPTH,
				text: getCodeBlockLabel(token),
				id: getHeadingAnchorId(messageId, tokenPath)
			});
		}
	});

	return headings;
}
