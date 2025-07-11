import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';
import { fetchVersion, fetchHostname, fetchRepo, fetchFfmpegVersion } from '../src/rpc/admin/vars';
import { fetchHome, fetchRoutes } from '../src/rpc/admin/links';

vi.mock('axios');
const mockedPost = axios.post as unknown as ReturnType<typeof vi.fn>;

describe('rpcClient', () => {
    it('fetchVersion posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { version: 'v9.9.9' } } });
        const res = await fetchVersion();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_version:1' }));
        expect(res.version).toBe('v9.9.9');
    });

    it('fetchHostname posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { hostname: 'unit-host' } } });
        const res = await fetchHostname();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_hostname:1' }));
        expect(res.hostname).toBe('unit-host');
    });

    it('fetchRepo posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { repo: 'https://repo' } } });
        const res = await fetchRepo();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_repo:1' }));
        expect(res.repo).toBe('https://repo');
    });

    it('fetchFfmpegVersion posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { ffmpeg_version: 'ffmpeg version 6.0' } } });
        const res = await fetchFfmpegVersion();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:vars:get_ffmpeg_version:1' }));
        expect(res.ffmpeg_version).toBe('ffmpeg version 6.0');
    });

    it('fetchHome posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { links: [] } } });
        const res = await fetchHome();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:links:get_home:1' }));
        expect(Array.isArray(res.links)).toBe(true);
    });

    it('fetchRoutes posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { routes: [] } } });
        const res = await fetchRoutes();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:admin:links:get_routes:1' }));
        expect(Array.isArray(res.routes)).toBe(true);
    });
});
