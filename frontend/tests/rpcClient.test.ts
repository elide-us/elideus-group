import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';
import { fetchVersion, fetchHostname, fetchRepo, fetchFfmpegVersion } from '../src/rpc/frontend/vars';
import { fetchHome, fetchRoutes } from '../src/rpc/frontend/links';
import { fetchList as fetchUsers, fetchProfile } from '../src/rpc/system/users';
import { fetchList as fetchConfigList, fetchSet as fetchConfigSet, fetchDelete as fetchConfigDelete } from '../src/rpc/system/config';

vi.mock('axios');
const mockedPost = axios.post as unknown as ReturnType<typeof vi.fn>;

describe('rpcClient', () => {
    it('fetchVersion posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { version: 'v9.9.9' } } });
        const res = await fetchVersion();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:vars:get_version:1' }), expect.anything());
        expect(res.version).toBe('v9.9.9');
    });

    it('fetchHostname posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { hostname: 'unit-host' } } });
        const res = await fetchHostname();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:vars:get_hostname:1' }), expect.anything());
        expect(res.hostname).toBe('unit-host');
    });

    it('fetchRepo posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { repo: 'https://repo' } } });
        const res = await fetchRepo();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:vars:get_repo:1' }), expect.anything());
        expect(res.repo).toBe('https://repo');
    });

    it('fetchFfmpegVersion posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { ffmpeg_version: 'ffmpeg version 6.0' } } });
        const res = await fetchFfmpegVersion();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:vars:get_ffmpeg_version:1' }), expect.anything());
        expect(res.ffmpeg_version).toBe('ffmpeg version 6.0');
    });

    it('fetchHome posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { links: [] } } });
        const res = await fetchHome();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:links:get_home:1' }), expect.anything());
        expect(Array.isArray(res.links)).toBe(true);
    });

    it('fetchRoutes posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { routes: [] } } });
        const res = await fetchRoutes();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:frontend:links:get_routes:1' }), expect.anything());
        expect(Array.isArray(res.routes)).toBe(true);
    });

    it('fetchUsers posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { users: [] } } });
        const res = await fetchUsers();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:system:users:list:1' }), expect.anything());
        expect(Array.isArray(res.users)).toBe(true);
    });

    it('fetchProfile posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { email: 'e' } } });
        const res = await fetchProfile({ userGuid: 'uid' });
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:system:users:get_profile:1' }), expect.anything());
        expect(res.email).toBe('e');
    });

    it('fetchConfigList posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { items: [] } } });
        const res = await fetchConfigList();
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:system:config:list:1' }), expect.anything());
        expect(Array.isArray(res.items)).toBe(true);
    });

    it('fetchConfigSet posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { items: [] } } });
        const res = await fetchConfigSet({ key: 'K', value: 'V' });
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:system:config:set:1' }), expect.anything());
        expect(Array.isArray(res.items)).toBe(true);
    });

    it('fetchConfigDelete posts correct request', async () => {
        mockedPost.mockResolvedValueOnce({ data: { payload: { items: [] } } });
        const res = await fetchConfigDelete({ key: 'K' });
        expect(mockedPost).toHaveBeenCalledWith('/rpc', expect.objectContaining({ op: 'urn:system:config:delete:1' }), expect.anything());
        expect(Array.isArray(res.items)).toBe(true);
    });
});
