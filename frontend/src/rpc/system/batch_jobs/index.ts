import { rpcCall } from '../../../shared/RpcModels';

export const fetchBatchJobs = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:list:1', payload);

export const fetchBatchJob = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:get:1', payload);

export const fetchUpsertBatchJob = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:upsert:1', payload);

export const fetchDeleteBatchJob = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:delete:1', payload);

export const fetchBatchJobHistory = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:list_history:1', payload);

export const fetchRunBatchJob = (payload: any = null): Promise<any> =>
	rpcCall('urn:system:batch_jobs:run_now:1', payload);
