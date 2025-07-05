import axios from 'axios';
import {
  AdminVarsHostname1,
  AdminVarsVersion1,
  RPCRequest,
  RPCResponse,
} from './generated_rpc_models';

const buildRequest = (op: string): RPCRequest => ({
  op,
  payload: null,
  version: 1,
  user_id: crypto.randomUUID(),
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

