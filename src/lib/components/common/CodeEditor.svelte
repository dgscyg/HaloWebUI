<script lang="ts">
	import { basicSetup, EditorView } from 'codemirror';
	import { keymap, placeholder } from '@codemirror/view';
	import { Compartment, EditorState } from '@codemirror/state';

	import { acceptCompletion } from '@codemirror/autocomplete';
	import { indentWithTab } from '@codemirror/commands';

	import {
		indentUnit,
		LanguageDescription,
		HighlightStyle,
		syntaxHighlighting
	} from '@codemirror/language';
	import { languages } from '@codemirror/language-data';
	import { tags } from '@lezer/highlight';

	import { oneDark } from '@codemirror/theme-one-dark';
	import { settings } from '$lib/stores';
	import {
		DEFAULT_HIGHLIGHTER_THEME,
		ensureShikiHighlighter,
		getEditorChromeTheme,
		normalizeHighlighterTheme,
		resolveRuntimeHighlighterThemeId,
		resolveShikiLanguage
	} from '$lib/utils/lobehub-chat-appearance';

	// GitHub Light 风格的浅色主题 (VS Code 风格优化)
	const githubLightHighlight = HighlightStyle.define([
		{ tag: tags.keyword, color: '#0070c1' },
		{ tag: tags.controlKeyword, color: '#af00db' },
		{ tag: tags.operatorKeyword, color: '#0070c1' },
		{ tag: tags.definitionKeyword, color: '#0070c1' },
		{ tag: tags.moduleKeyword, color: '#af00db' },
		{ tag: tags.comment, color: '#6a737d', fontStyle: 'italic' },
		{ tag: tags.string, color: '#a31515' },
		{ tag: tags.number, color: '#098658' },
		{ tag: tags.bool, color: '#0070c1' },
		{ tag: tags.null, color: '#0070c1' },
		{ tag: tags.function(tags.variableName), color: '#795e26' },
		{ tag: tags.function(tags.propertyName), color: '#795e26' },
		{ tag: tags.definition(tags.variableName), color: '#001080' },
		{ tag: tags.definition(tags.propertyName), color: '#001080' },
		{ tag: tags.variableName, color: '#001080' },
		{ tag: tags.propertyName, color: '#001080' },
		{ tag: tags.className, color: '#267f99' },
		{ tag: tags.typeName, color: '#267f99' },
		{ tag: tags.tagName, color: '#800000' },
		{ tag: tags.attributeName, color: '#e50000' },
		{ tag: tags.operator, color: '#000000' },
		{ tag: tags.punctuation, color: '#000000' },
		{ tag: tags.bracket, color: '#000000' },
		{ tag: tags.meta, color: '#af00db' },
		{ tag: tags.atom, color: '#0070c1' },
		{ tag: tags.self, color: '#0070c1' },
		{ tag: tags.special(tags.variableName), color: '#af00db' },
		{ tag: tags.regexp, color: '#811f3f' },
		{ tag: tags.escape, color: '#ee0000' },
		{ tag: tags.link, color: '#0070c1', textDecoration: 'underline' },
		{ tag: tags.heading, color: '#800000', fontWeight: 'bold' }
	]);
	const githubLight = [syntaxHighlighting(githubLightHighlight)];

	import { onMount, getContext, tick } from 'svelte';

	import { formatPythonCode } from '$lib/apis/utils';
	import { toast } from 'svelte-sonner';

	const i18n = getContext('i18n');

	export let boilerplate = '';
	export let value = '';
	export let useShikiTheme = true;

	export let onSave = () => {};
	export let onChange = () => {};

	let _value = '';
	let suppressDocChangeCallback = false;

	$: if (value !== undefined && value !== null) {
		updateValue();
	}

	const isEditorUpdateInProgressError = (error: unknown) =>
		error instanceof Error &&
		error.message.includes('Calls to EditorView.update are not allowed while an update is in progress');

	const queueEditorDispatch = (callback: () => void, attempt = 0) => {
		window.setTimeout(() => {
			if (!codeEditor) {
				return;
			}

			try {
				callback();
			} catch (error) {
				if (isEditorUpdateInProgressError(error) && attempt < 5) {
					queueEditorDispatch(callback, attempt + 1);
					return;
				}

				throw error;
			}
		}, 0);
	};

	const dispatchEditorChanges = (spec: any, attempt = 0) => {
		if (!codeEditor) {
			return;
		}

		try {
			codeEditor.dispatch(spec);
		} catch (error) {
			if (isEditorUpdateInProgressError(error) && attempt < 5) {
				queueEditorDispatch(() => {
					dispatchEditorChanges(spec, attempt + 1);
				});
				return;
			}

			throw error;
		}
	};

	const updateValue = () => {
		if (_value !== value) {
			_value = value;

			if (codeEditor) {
				const nextValue = String(value ?? '');
				queueEditorDispatch(() => {
					if (!codeEditor) {
						return;
					}

					const currentDoc = codeEditor.state.doc.toString();
					if (currentDoc === nextValue) {
						return;
					}

					const changes = findChanges(currentDoc, nextValue);
					if (changes.length === 0) {
						return;
						}

						suppressDocChangeCallback = true;
						try {
							dispatchEditorChanges({ changes });
						} finally {
							window.setTimeout(() => {
								suppressDocChangeCallback = false;
						}, 0);
					}
				});
			}
		}
	};

	/**
	 * Finds multiple diffs in two strings and generates minimal change edits.
	 */
	function findChanges(oldStr, newStr) {
		let changes = [];
		let oldIndex = 0,
			newIndex = 0;

		while (oldIndex < oldStr.length || newIndex < newStr.length) {
			if (oldStr[oldIndex] !== newStr[newIndex]) {
				let start = oldIndex;

				// Identify the changed portion
				while (oldIndex < oldStr.length && oldStr[oldIndex] !== newStr[newIndex]) {
					oldIndex++;
				}
				while (newIndex < newStr.length && newStr[newIndex] !== oldStr[start]) {
					newIndex++;
				}

				changes.push({
					from: start,
					to: oldIndex, // Replace the differing part
					insert: newStr.substring(start, newIndex)
				});
			} else {
				oldIndex++;
				newIndex++;
			}
		}

		return changes;
	}

	export let id = '';
	export let lang = '';

	let codeEditor;

	export const focus = () => {
		codeEditor.focus();
	};

	let isDarkMode = false;
	let editorLanguage = new Compartment();
	let editorChromeTheme = new Compartment();
	let editorSyntaxTheme = new Compartment();
	let themeApplyRequestId = 0;

	languages.push(
		LanguageDescription.of({
			name: 'HCL',
			extensions: ['hcl', 'tf'],
			load() {
				return import('codemirror-lang-hcl').then((m) => m.hcl());
			}
		})
	);
	languages.push(
		LanguageDescription.of({
			name: 'Elixir',
			extensions: ['ex', 'exs'],
			load() {
				return import('codemirror-lang-elixir').then((m) => m.elixir());
			}
		})
	);

	const getLang = async () => {
		const normalizedLang = String(lang ?? '').trim().toLowerCase();
		const language = languages.find((l) => {
			const aliases = l.alias?.map((alias) => alias.toLowerCase()) ?? [];
			const extensions = l.extensions?.map((extension) => extension.toLowerCase()) ?? [];
			return (
				l.name?.toLowerCase() === normalizedLang ||
				aliases.includes(normalizedLang) ||
				extensions.includes(normalizedLang)
			);
		});
		return await language?.load();
	};

	export const formatPythonCodeHandler = async () => {
		if (codeEditor) {
			const res = await formatPythonCode(localStorage.token, _value).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res && res.code) {
				const formattedCode = res.code;
				dispatchEditorChanges({
					changes: [{ from: 0, to: codeEditor.state.doc.length, insert: formattedCode }]
				});

				_value = formattedCode;
				onChange(_value);
				await tick();

				toast.success($i18n.t('Code formatted successfully'));
				return true;
			}
			return false;
		}
		return false;
	};

	let extensions = [
		basicSetup,
		keymap.of([{ key: 'Tab', run: acceptCompletion }, indentWithTab]),
		indentUnit.of('    '),
		placeholder('Enter your code here...'),
		EditorView.updateListener.of((e) => {
			if (e.docChanged) {
				_value = e.state.doc.toString();
				if (!suppressDocChangeCallback) {
					onChange(_value);
				}
			}
		}),
		editorChromeTheme.of([]),
		editorSyntaxTheme.of([]),
		editorLanguage.of([])
	];

	const applyEditorTheme = async () => {
		if (!codeEditor || typeof document === 'undefined') return;

		const darkMode = document.documentElement.classList.contains('dark');
		if (!useShikiTheme) {
			await applyFallbackTheme(darkMode);
			return;
		}

		await applyHighlighterTheme();
	};

	$: if (lang) {
		setLanguage();
		applyEditorTheme();
	}

	$: if (codeEditor) {
		$settings?.highlighterTheme;
		useShikiTheme;
		applyEditorTheme();
	}

	const setLanguage = async () => {
		const language = await getLang();
		if (language && codeEditor) {
			queueEditorDispatch(() => {
				dispatchEditorChanges({
					effects: editorLanguage.reconfigure(language)
				});
			});
		}
	};

	const buildEditorChromeExtension = (chromeTheme, darkMode: boolean) =>
		EditorView.theme(
			{
				'&': {
					backgroundColor: chromeTheme.surface.background,
					color: chromeTheme.surface.foreground,
					height: '100%'
				},
				'.cm-activeLine': {
					backgroundColor: chromeTheme.lineHighlight
				},
				'.cm-activeLineGutter': {
					backgroundColor: chromeTheme.lineHighlight,
					color: chromeTheme.surface.foreground
				},
				'.cm-content': {
					caretColor: chromeTheme.caret,
					fontFamily: chromeTheme.fontFamily,
					minHeight: '100%',
					padding: '12px 14px'
				},
				'.cm-cursor, .cm-dropCursor': {
					borderLeftColor: chromeTheme.caret
				},
				'.cm-focused .cm-selectionBackground, .cm-line::selection, .cm-selectionLayer .cm-selectionBackground':
					{
						backgroundColor: chromeTheme.selection
					},
				'.cm-gutters': {
					backgroundColor: chromeTheme.surface.background,
					border: 'none',
					color: chromeTheme.gutterForeground
				},
				'.cm-placeholder': {
					color: chromeTheme.gutterForeground
				},
				'.cm-scroller': {
					backgroundColor: chromeTheme.surface.background,
					color: chromeTheme.surface.foreground,
					fontFamily: chromeTheme.fontFamily,
					overflow: 'auto'
				},
				'.cm-selectionBackground, ::selection': {
					backgroundColor: chromeTheme.selection
				}
			},
			{ dark: darkMode }
		);

	const applyFallbackTheme = async (darkMode: boolean) => {
		if (!codeEditor) return;

		const chromeTheme = await getEditorChromeTheme(DEFAULT_HIGHLIGHTER_THEME, darkMode);
		queueEditorDispatch(() => {
			dispatchEditorChanges({
				effects: [
					editorChromeTheme.reconfigure(buildEditorChromeExtension(chromeTheme, darkMode)),
					editorSyntaxTheme.reconfigure(darkMode ? oneDark : githubLight)
				]
			});
		});
	};

	const applyHighlighterTheme = async () => {
		if (!codeEditor || typeof document === 'undefined') return;

		const currentRequestId = ++themeApplyRequestId;
		const darkMode = document.documentElement.classList.contains('dark');
		const selectedTheme = normalizeHighlighterTheme(
			$settings?.highlighterTheme ?? DEFAULT_HIGHLIGHTER_THEME
		);
		const runtimeThemeId = resolveRuntimeHighlighterThemeId(selectedTheme, darkMode);

		try {
			const [shikiModule, highlighter, resolvedLanguage, chromeTheme] = await Promise.all([
				import('codemirror-shiki'),
				ensureShikiHighlighter(lang, selectedTheme, darkMode),
				resolveShikiLanguage(lang),
				getEditorChromeTheme(selectedTheme, darkMode)
			]);

			if (!codeEditor || currentRequestId !== themeApplyRequestId) return;

				queueEditorDispatch(() => {
					if (!codeEditor || currentRequestId !== themeApplyRequestId) return;

					dispatchEditorChanges({
						effects: [
							editorChromeTheme.reconfigure(buildEditorChromeExtension(chromeTheme, darkMode)),
							editorSyntaxTheme.reconfigure(
							shikiModule.default({
								highlighter,
								language: resolvedLanguage,
								theme: runtimeThemeId
							})
						)
					]
				});
			});
		} catch (error) {
			console.error('Failed to apply shiki theme to CodeMirror', error);
			if (!codeEditor || currentRequestId !== themeApplyRequestId) return;
			await applyFallbackTheme(darkMode);
		}
	};

	onMount(() => {
		if (value === '') {
			value = boilerplate;
		}

		_value = value;

		// Check if html class has dark mode
		isDarkMode = document.documentElement.classList.contains('dark');

		// python code editor, highlight python code
		codeEditor = new EditorView({
			state: EditorState.create({
				doc: _value,
				extensions: extensions
			}),
			parent: document.getElementById(`code-textarea-${id}`)
		});

		void applyEditorTheme();

		// listen to html class changes this should fire only when dark mode is toggled
		const observer = new MutationObserver((mutations) => {
			mutations.forEach((mutation) => {
				if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
					const _isDarkMode = document.documentElement.classList.contains('dark');

					if (_isDarkMode !== isDarkMode) {
						isDarkMode = _isDarkMode;
						void applyEditorTheme();
					}
				}
			});
		});

		observer.observe(document.documentElement, {
			attributes: true,
			attributeFilter: ['class']
		});

		const keydownHandler = async (e) => {
			if ((e.ctrlKey || e.metaKey) && e.key === 's') {
				e.preventDefault();

				onSave();
			}

			// Format code when Ctrl + Shift + F is pressed
			if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'f') {
				e.preventDefault();
				await formatPythonCodeHandler();
			}
		};

		document.addEventListener('keydown', keydownHandler);

		return () => {
			observer.disconnect();
			document.removeEventListener('keydown', keydownHandler);
		};
	});
</script>

<div id="code-textarea-{id}" class="h-full w-full text-sm" />
