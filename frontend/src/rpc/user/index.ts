import { rpcCall, FrontendUserProfileData1, FrontendUserSetDisplayName1 } from '../../shared/RpcModels';

export const fetchUserProfile = (payload: any = null): Promise<FrontendUserProfileData1> =>
rpcCall('urn:frontend:user:get_profile:1', payload);

export const updateDisplayName = (payload: FrontendUserSetDisplayName1): Promise<void> =>
rpcCall('urn:frontend:user:set_display_name:1', payload);

export const updateDisplayEmail = (payload: any = null): Promise<void> =>
rpcCall('urn:frontend:user:set_display_email:1', payload);

export const setPrimaryProvider = (payload: any = null): Promise<void> =>
rpcCall('urn:frontend:user:set_primary_provider:1', payload);

export const linkProvider = (payload: any = null): Promise<void> =>
rpcCall('urn:frontend:user:link_provider:1', payload);

export const unlinkProvider = (payload: any = null): Promise<void> =>
rpcCall('urn:frontend:user:unlink_provider:1', payload);

export const deleteAccount = (payload: any = null): Promise<void> =>
rpcCall('urn:frontend:user:delete_account:1', payload);
