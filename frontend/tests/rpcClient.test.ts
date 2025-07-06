import { describe, it, expect, vi, beforeAll } from 'vitest';
import axios from 'axios';
import { fetchVersion, fetchHostname, fetchFfmpegVersion } from '../src/rpcClient';

vi.mock('axios');

const mockedPost = axios.post as unknown as ReturnType<typeof vi.fn>;

describe('rpcClient', () => {
	it('fetchVersion posts correct request', async () => {
		mockedPost.mockResolvedValueOnce({ data: { payload: { version: '1.0.0' } } });
		const res = await fetchVersion();
		expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_version:1' }));
		expect(res.version).toBe('1.0.0');
	});

        it('fetchHostname posts correct request', async () => {
                mockedPost.mockResolvedValueOnce({ data: { payload: { hostname: 'host' } } });
                const res = await fetchHostname();
                expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_hostname:1' }));
                expect(res.hostname).toBe('host');
        });

        it('fetchFfmpegVersion posts correct request', async () => {
                mockedPost.mockResolvedValueOnce({ data: { payload: { ffmpeg_version: 'ffmpeg version 6.0' } } });
                const res = await fetchFfmpegVersion();
                expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_ffmpeg_version:1' }));
                expect(res.ffmpeg_version).toBe('ffmpeg version 6.0');
        });
});
