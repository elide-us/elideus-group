export interface RPCRequest {
  op: string;
  payload: any;
  version: number;
  user_id: any;
  timestamp: any;
  metadata: any;
}

export interface RPCResponse {
  op: string;
  payload: any;
  version: number;
  timestamp: any;
  metadata: any;
}

export interface AdminVarsHostname1 {
  hostname: string;
}

export interface AdminVarsVersion1 {
  version: string;
}

