import { useContext, useEffect, useState } from 'react';
import {
       Container,
       Paper,
       TextField,
       Typography,
       Switch,
       FormControlLabel,
       Radio,
       Button,
       Stack,
       Avatar
} from '@mui/material';
import UserContext from './shared/UserContext';
import Notification from './shared/Notification';
import type { FrontendUserProfileData1 } from './shared/RpcModels';
import {
	fetchUserProfile,
	updateDisplayName,
	updateDisplayEmail,
	setPrimaryProvider,
	linkProvider,
	unlinkProvider,
	deleteAccount
} from './rpc/user';

const PROVIDERS = ['microsoft', 'discord', 'google', 'apple'];

const UserPage = (): JSX.Element => {
	const { userData } = useContext(UserContext);
	const [profile, setProfile] = useState<FrontendUserProfileData1 | null>(null);
	const [notification, setNotification] = useState({
		open: false,
		severity: 'info' as 'info' | 'success' | 'warning' | 'error',
		message: ''
	});

	useEffect(() => {
		void (async () => {
			try {
				const res = await fetchUserProfile();
				setProfile(res);
			} catch {
				if (userData) {
					setProfile({
						displayName: userData.username,
						providerUsername: userData.username,
						displayEmail: true,
						email: userData.email,
                                               primaryProvider: userData.defaultProvider,
                                               linkedProviders: [userData.defaultProvider],
                                               profilePicture: userData.profilePicture ?? null,
                                               credits: Number(userData.credits ?? 0),
                                               storageUsed: 0,
                                               storageQuota: 0
                                       });
				}
			}
		})();
	}, [userData]);

	const handleNotificationClose = (): void => {
		setNotification(prev => ({ ...prev, open: false }));
	};

	const handleDisplayNameChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
		setProfile(prev => prev ? { ...prev, displayName: e.target.value } : prev);
	};

	const handleDisplayEmailToggle = (e: React.ChangeEvent<HTMLInputElement>): void => {
		setProfile(prev => prev ? { ...prev, displayEmail: e.target.checked } : prev);
	};

	const handlePrimaryProviderChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
		setProfile(prev => prev ? { ...prev, primaryProvider: e.target.value } : prev);
	};

	const handleSave = async (): Promise<void> => {
               if (!profile || !userData) return;
               try {
                       await updateDisplayName({ bearerToken: userData.bearerToken, displayName: profile.displayName });
               } catch {}
               try { await updateDisplayEmail({ displayEmail: profile.displayEmail }); } catch {}
		try { await setPrimaryProvider({ provider: profile.primaryProvider }); } catch {}
		setNotification({ open: true, severity: 'success', message: 'Profile updated.' });
	};

	const handleLink = async (provider: string): Promise<void> => {
		try { await linkProvider({ provider }); } catch {}
	};

	const handleUnlink = async (provider: string): Promise<void> => {
		try { await unlinkProvider({ provider }); } catch {}
	};

	const handleDeleteAccount = async (): Promise<void> => {
		try { await deleteAccount(); } catch {}
	};

	if (!profile) return <></>;

	return (
		<Container sx={{ py: 4 }}>
       <Paper sx={{ p: 2 }}>
               <Stack spacing={2}>
                       <Stack direction='row' spacing={2} alignItems='center'>
                               {userData?.profilePicture && (
                                       <Avatar src={`data:image/png;base64,${userData.profilePicture}`} />
                               )}
                               <TextField label='Display Name' fullWidth value={profile.displayName} onChange={handleDisplayNameChange} />
                       </Stack>
                       <Typography variant='body2'>Provider Username: {profile.providerUsername}</Typography>
                       <FormControlLabel control={<Switch checked={profile.displayEmail} onChange={handleDisplayEmailToggle} />} label='Display my email' />
                       {PROVIDERS.map(p => (
                               <Stack key={p} direction='row' spacing={1} alignItems='center'>
                                       <FormControlLabel value={p} control={<Radio checked={profile.primaryProvider === p} onChange={handlePrimaryProviderChange} />} label={p} />
                                       {profile.linkedProviders.includes(p) ? (
                                               <Button variant='outlined' onClick={() => handleUnlink(p)}>Unlink</Button>
                                       ) : (
                                               <Button variant='contained' onClick={() => handleLink(p)}>Link</Button>
                                       )}
                               </Stack>
                       ))}
					<Typography>Credits: {profile.credits}</Typography>
					<Typography>Storage: {profile.storageUsed} / {profile.storageQuota}</Typography>
					<Button variant='contained' onClick={handleSave}>Save</Button>
					<Button variant='outlined' color='error' onClick={handleDeleteAccount}>Delete Account</Button>
				</Stack>
			</Paper>
			<Notification
				open={notification.open}
				handleClose={handleNotificationClose}
				severity={notification.severity}
				message={notification.message}
			/>
		</Container>
	);
};

export default UserPage;