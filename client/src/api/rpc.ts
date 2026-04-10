import axios from 'axios';

import type { PathNode } from '../engine/types';

interface LoadPathResult {
	pathData: PathNode;
	componentData: Record<string, unknown>;
}

interface RpcEnvelope<TPayload> {
	op: string;
	payload: TPayload;
	version: number;
	timestamp?: string;
}

export async function loadPath(path: string): Promise<LoadPathResult> {
	const response = await axios.post<RpcEnvelope<LoadPathResult>>('/rpc', {
		op: 'urn:public:route:load_path:1',
		payload: {
			path,
		},
		version: 1,
		timestamp: new Date().toISOString(),
	});
	return response.data.payload;
}
