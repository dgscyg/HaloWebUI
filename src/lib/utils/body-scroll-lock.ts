let lockCount = 0;
let previousBodyOverflow = '';
let previousBodyPaddingInlineEnd = '';

const getScrollbarWidth = () => {
	if (typeof window === 'undefined' || typeof document === 'undefined') return 0;

	return Math.max(0, window.innerWidth - document.documentElement.clientWidth);
};

export const lockBodyScroll = () => {
	if (typeof window === 'undefined' || typeof document === 'undefined') return;

	if (lockCount === 0) {
		const { body } = document;
		const computedPaddingInlineEnd = Number.parseFloat(
			window.getComputedStyle(body).paddingInlineEnd || '0'
		);
		const scrollbarWidth = getScrollbarWidth();

		previousBodyOverflow = body.style.overflow;
		previousBodyPaddingInlineEnd = body.style.paddingInlineEnd;

		body.style.overflow = 'hidden';

		if (scrollbarWidth > 0) {
			body.style.paddingInlineEnd = `${computedPaddingInlineEnd + scrollbarWidth}px`;
		}
	}

	lockCount += 1;
};

export const unlockBodyScroll = () => {
	if (typeof document === 'undefined' || lockCount === 0) return;

	lockCount -= 1;

	if (lockCount === 0) {
		const { body } = document;

		body.style.overflow = previousBodyOverflow;
		body.style.paddingInlineEnd = previousBodyPaddingInlineEnd;

		previousBodyOverflow = '';
		previousBodyPaddingInlineEnd = '';
	}
};
