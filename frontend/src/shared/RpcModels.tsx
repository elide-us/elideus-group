export interface RPCRequest {
  op: string;
  payload: any;
  version: number;
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

export interface UserData {
  bearerToken: string;
}

export interface AdminLinksHome1 {
  links: any;
}

export interface AdminLinksRoutes1 {
  routes: any;
}

export interface LinkItem {
  title: string;
  url: string;
}

export interface RouteItem {
  path: string;
  name: string;
  icon: string;
}

export interface AdminVarsFfmpegVersion1 {
  ffmpeg_version: string;
}

export interface AdminVarsHostname1 {
  hostname: string;
}

export interface AdminVarsRepo1 {
  repo: string;
}

export interface AdminVarsVersion1 {
  version: string;
}
