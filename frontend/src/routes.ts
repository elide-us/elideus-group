import type { RouteItem, AdminLinksRoutes1 } from './shared/RpcModels';
import { fetchRoutes } from './rpcClient';

export const getRoutes = async (): Promise<RouteItem[]> => {
    try {
        const res: AdminLinksRoutes1 = await fetchRoutes();
        return res.routes;
    } catch {
        return [];
    }
};
