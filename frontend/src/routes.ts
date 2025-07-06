import type { RouteItem, AdminLinksRoutes1 } from './shared/RpcModels';
import { fetchRoutes } from './rpc/admin/links';

export const getRoutes = async (): Promise<RouteItem[]> => {
    try {
        const res: AdminLinksRoutes1 = await fetchRoutes();
        return res.routes;
    } catch {
        return [];
    }
};
