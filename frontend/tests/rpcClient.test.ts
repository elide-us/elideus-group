import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';
import { fetchVersion, fetchHostname, fetchFfmpegVersion, fetchHomeLinks } from '../src/rpcClient';

vi.mock('axios');

const mockedPost = axios.post as unknown as ReturnType<typeof vi.fn>;

describe('rpcClient', () => {
	it('fetchVersion posts correct request', async () => {
		mockedPost.mockResolvedValueOnce({ data: { payload: { version: '9.9.9' } } });
		const res = await fetchVersion();
		expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_version:1' }));
		expect(res.version).toBe('9.9.9');
	});

        it('fetchHostname posts correct request', async () => {
                mockedPost.mockResolvedValueOnce({ data: { payload: { hostname: 'unit-host' } } });
                const res = await fetchHostname();
                expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_hostname:1' }));
                expect(res.hostname).toBe('unit-host');
        });

        it('fetchFfmpegVersion posts correct request', async () => {
                mockedPost.mockResolvedValueOnce({ data: { payload: { ffmpeg_version: 'ffmpeg version 6.0' } } });
                const res = await fetchFfmpegVersion();
                expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_ffmpeg_version:1' }));
                expect(res.ffmpeg_version).toBe('ffmpeg version 6.0');
        });

        it('fetchHomeLinks posts correct request', async () => {
                mockedPost.mockResolvedValueOnce({ data: { payload: { links: [] } } });
                const res = await fetchHomeLinks();
                expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:links:get_home:1' }));
                expect(Array.isArray(res.links)).toBe(true);
        });
});
