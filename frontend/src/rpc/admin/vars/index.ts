// ================================================
// WARNING: This file is automatically generated.
// Do not modify it by hand. Your changes will be
// overwritten the next time the generator runs.
// ================================================

import axios from 'axios';
import { RPCRequest, RPCResponse, AdminVarsFfmpegVersion1, AdminVarsHostname1, AdminVarsRepo1, AdminVarsVersion1 } from '../../../shared/RpcModels';

const rpcCall = async <T>(op: string): Promise<T> => {
    const request: RPCRequest = {
        op,
        payload: null,
        version: 1,
        timestamp: Date.now(),
        metadata: null,
    };
    const response = await axios.post<RPCResponse>('/rpc', request);
    return response.data.payload as T;
};

export const fetchVersion = (): Promise<AdminVarsVersion1> => rpcCall('urn:admin:vars:get_version:1');
export const fetchHostname = (): Promise<AdminVarsHostname1> => rpcCall('urn:admin:vars:get_hostname:1');
export const fetchRepo = (): Promise<AdminVarsRepo1> => rpcCall('urn:admin:vars:get_repo:1');
export const fetchFfmpegVersion = (): Promise<AdminVarsFfmpegVersion1> => rpcCall('urn:admin:vars:get_ffmpeg_version:1');
