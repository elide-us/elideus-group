export interface RPCRequest {
  op: string;
  payload: any | null;
  version: number;
  timestamp: any | null;
  metadata: any | null;
}
export interface RPCResponse {
  op: string;
  payload: any;
  version: number;
  timestamp: any;
  metadata: any | null;
}
export interface UserData {
  bearerToken: string;
}
export interface AdminLinksHome1 {
  links: LinkItem[];
}
export interface LinkItem {
  title: string;
  url: string;
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