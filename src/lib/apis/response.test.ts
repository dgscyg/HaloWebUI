import { describe, expect, it } from 'vitest';

import {
	createResponseError,
	ensureOkResponse,
	parseArrayBufferResponse,
	parseBlobResponse,
	parseJsonResponse,
	parseTextResponse
} from './response';

describe('response helpers', () => {
	it('parses successful json payloads without using response.json()', async () => {
		const response = new Response(JSON.stringify({ ok: true, value: 42 }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});

		await expect(parseJsonResponse(response)).resolves.toEqual({ ok: true, value: 42 });
	});

	it('surfaces plain-text 500 errors as detail instead of a JSON parse failure', async () => {
		const response = new Response('Internal Server Error', {
			status: 500,
			statusText: 'Internal Server Error',
			headers: { 'Content-Type': 'text/plain' }
		});

		await expect(parseJsonResponse(response)).rejects.toMatchObject({
			detail: 'Internal Server Error',
			status: 500,
			statusText: 'Internal Server Error'
		});
	});

	it('preserves nested provider error messages in the normalized detail', () => {
		const response = new Response(null, {
			status: 401,
			statusText: 'Unauthorized'
		});

		expect(createResponseError(response, { error: { message: 'Bad key' } })).toMatchObject({
			detail: 'Bad key',
			error: { message: 'Bad key' },
			status: 401
		});
	});

	it('parses blob and array-buffer responses while normalizing error branches', async () => {
		const blobResponse = new Response('csv,data', { status: 200 });
		const blob = await parseBlobResponse(blobResponse);
		await expect(blob.text()).resolves.toBe('csv,data');

		const bufferResponse = new Response('abc', { status: 200 });
		const buffer = await parseArrayBufferResponse(bufferResponse);
		expect(new TextDecoder().decode(buffer)).toBe('abc');
	});

	it('keeps successful raw responses intact and normalizes text errors', async () => {
		const okResponse = new Response('done', { status: 200 });
		await expect(ensureOkResponse(okResponse)).resolves.toBe(okResponse);

		const errorResponse = new Response('Gateway timeout', {
			status: 504,
			statusText: 'Gateway Timeout'
		});
		await expect(parseTextResponse(errorResponse)).rejects.toMatchObject({
			detail: 'Gateway timeout',
			status: 504
		});
	});
});
