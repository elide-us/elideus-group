export interface RPCRequest {
  op: string;
  payload: unknown;
  version: number;
  user_id: unknown;
  timestamp: unknown;
  metadata: unknown;
}

export interface RPCResponse {
  op: string;
  payload: unknown;
  version: number;
  timestamp: unknown;
  metadata: unknown;
}

export interface AdminVarsHostname1 {
  hostname: string;
}

export interface AdminVarsVersion1 {
  version: string;
}
