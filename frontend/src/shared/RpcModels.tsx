// ================================================
// WARNING: This file is automatically generated.
// Do not modify it by hand. Your changes will be
// overwritten the next time the generator runs.
// ================================================

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
export interface AdminLinksRoutes1 {
  routes: RouteItem[];
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
export interface AuthMicrosoftLoginData1 {
  bearerToken: string;
  defaultProvider: string;
  username: string;
  email: string;
  backupEmail: string | null;
  profilePicture: string | null;
  credits: number | null;
}