// ================================================
// WARNING: This file is automatically generated.
// Do not modify it by hand. Your changes will be
// overwritten the next time the generator runs.
// ================================================

import { rpcCall, SystemRoutesList1 } from '../../../shared/RpcModels';

export const fetchList = (payload: any = null): Promise<SystemRoutesList1> => rpcCall('urn:system:routes:list:1', payload);
export const fetchSet = (payload: any = null): Promise<any> => rpcCall('urn:system:routes:set:1', payload);
export const fetchDelete = (payload: any = null): Promise<any> => rpcCall('urn:system:routes:delete:1', payload);
