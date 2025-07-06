import axios from 'axios';
import {
        AdminVarsHostname1,
        AdminVarsRepo1,
        AdminVarsVersion1,
        AdminVarsFfmpegVersion1,
        RPCRequest,
        RPCResponse,
} from './shared/RpcModels';


const buildRequest = (op: string): RPCRequest => ({
    op,
    payload: null,
    version: 1,
    timestamp: Date.now(),
    metadata: null,
});

export const fetchVersion = async (): Promise<AdminVarsVersion1> => {
    const request = buildRequest('urn:admin:vars:get_version:1');
    const response = await axios.post<RPCResponse>('/rpc', request);
    return response.data.payload as AdminVarsVersion1;
};

export const fetchHostname = async (): Promise<AdminVarsHostname1> => {
    const request = buildRequest('urn:admin:vars:get_hostname:1');
    const response = await axios.post<RPCResponse>('/rpc', request);
    return response.data.payload as AdminVarsHostname1;
};

export const fetchRepo = async (): Promise<AdminVarsRepo1> => {
    const request = buildRequest('urn:admin:vars:get_repo:1');
    const response = await axios.post<RPCResponse>('/rpc', request);
    return response.data.payload as AdminVarsRepo1;
};

export const fetchFfmpegVersion = async (): Promise<AdminVarsFfmpegVersion1> => {
    const request = buildRequest('urn:admin:vars:get_ffmpeg_version:1');
    const response = await axios.post<RPCResponse>('/rpc', request);
    return response.data.payload as AdminVarsFfmpegVersion1;
};
