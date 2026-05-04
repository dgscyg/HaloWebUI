const DEFAULT_IDLE_MS = 800;

type InitScrollbarAutohideOptions = {
	idleMs?: number;
};

export function initScrollbarAutohide(options: InitScrollbarAutohideOptions = {}) {
	if (typeof window === 'undefined') return () => {};

	const idleMs = options.idleMs ?? DEFAULT_IDLE_MS;
	const timers = new Map<HTMLElement, number>();
	const hovered = new WeakSet<HTMLElement>();
	const scrollableCache = new WeakMap<HTMLElement, HTMLElement | null>();

	const setVisible = (element: HTMLElement) => {
		element.dataset.scrollbars = 'visible';

		const existing = timers.get(element);
		if (existing !== undefined) window.clearTimeout(existing);

		// Don't start fade-out timer if mouse is still hovering
		if (hovered.has(element)) return;

		const timer = window.setTimeout(() => {
			delete element.dataset.scrollbars;
			timers.delete(element);
		}, idleMs);

		timers.set(element, timer);
	};

	const clearVisible = (element: HTMLElement) => {
		const existing = timers.get(element);
		if (existing !== undefined) window.clearTimeout(existing);

		const timer = window.setTimeout(() => {
			delete element.dataset.scrollbars;
			timers.delete(element);
		}, idleMs);

		timers.set(element, timer);
	};

	const resolveScrollTarget = (target: EventTarget | null): HTMLElement | null => {
		if (!target) return null;
		if (target === window || target === document) {
			const el = document.scrollingElement;
			return el instanceof HTMLElement ? el : null;
		}
		return target instanceof HTMLElement ? target : null;
	};

	const isScrollable = (el: HTMLElement): boolean => {
		const style = getComputedStyle(el);
		const overflowY = style.overflowY;
		const overflowX = style.overflowX;
		const canScrollY =
			(overflowY === 'auto' || overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
		const canScrollX =
			(overflowX === 'auto' || overflowX === 'scroll') && el.scrollWidth > el.clientWidth;
		return canScrollY || canScrollX;
	};

	// Find the nearest scrollable ancestor (including the element itself) with caching
	const findScrollableAncestor = (el: HTMLElement): HTMLElement | null => {
		// Check cache first
		if (scrollableCache.has(el)) {
			return scrollableCache.get(el)!;
		}

		let current: HTMLElement | null = el;
		while (current) {
			if (isScrollable(current)) {
				scrollableCache.set(el, current);
				return current;
			}
			current = current.parentElement;
		}

		scrollableCache.set(el, null);
		return null;
	};

	// Scroll handler
	const onScroll = (event: Event) => {
		const target = resolveScrollTarget(event.target);
		if (!target) return;
		setVisible(target);
	};

	// Hover handlers with relatedTarget check to avoid flicker
	const onMouseEnter = (event: MouseEvent) => {
		const target = event.target;
		if (!(target instanceof HTMLElement)) return;

		const scrollable = findScrollableAncestor(target);
		if (!scrollable) return;

		// Check if we're coming from inside the same scrollable container
		const relatedTarget = event.relatedTarget;
		if (relatedTarget instanceof HTMLElement) {
			const relatedScrollable = findScrollableAncestor(relatedTarget);
			if (relatedScrollable === scrollable) {
				// Still inside the same container, already tracked
				return;
			}
		}

		hovered.add(scrollable);
		setVisible(scrollable);
	};

	const onMouseLeave = (event: MouseEvent) => {
		const target = event.target;
		if (!(target instanceof HTMLElement)) return;

		const scrollable = findScrollableAncestor(target);
		if (!scrollable) return;

		// Check if we're moving to another element inside the same scrollable container
		const relatedTarget = event.relatedTarget;
		if (relatedTarget instanceof HTMLElement) {
			const relatedScrollable = findScrollableAncestor(relatedTarget);
			if (relatedScrollable === scrollable) {
				// Still inside the same container, don't hide
				return;
			}
		}

		hovered.delete(scrollable);
		clearVisible(scrollable);
	};

	window.addEventListener('scroll', onScroll, { capture: true, passive: true });
	document.addEventListener('mouseover', onMouseEnter, { passive: true });
	document.addEventListener('mouseout', onMouseLeave, { passive: true });

	return () => {
		window.removeEventListener('scroll', onScroll, true);
		document.removeEventListener('mouseover', onMouseEnter);
		document.removeEventListener('mouseout', onMouseLeave);
		for (const [element, timer] of timers) {
			window.clearTimeout(timer);
			delete element.dataset.scrollbars;
		}
		timers.clear();
	};
}
