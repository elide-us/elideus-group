import { useState, useContext, useEffect } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { Login as LoginIcon } from '@mui/icons-material';
import { Typography, Box, Tooltip, IconButton, ListItemText } from '@mui/material';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig } from './config/msal';
import { fetchInvalidateToken } from './rpc/auth/session';
import { fetchProfile } from './rpc/users/profile';
import Notification from './Notification';
import UserContext from './shared/UserContext';
import type { UsersProfileProfile1 } from './shared/RpcModels';

const pca = new PublicClientApplication(msalConfig);

interface LoginProps {
	open: boolean;
}

const Login = ({ open }: LoginProps): JSX.Element => {
	const { userData, clearUserData } = useContext(UserContext);
	const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
	const [notification, setNotification] = useState({
		open: false,
		severity: 'info' as 'info' | 'success' | 'warning' | 'error',
		message: ''
	});
	const handleNotificationClose = (): void => {
		setNotification(prev => ({ ...prev, open: false }));
	};
	const navigate = useNavigate();
	const handleLoginNavigation = (): void => {
		navigate('/loginpage');
	};
	useEffect(() => {
		let active = true;
		if (userData) {
			fetchProfile()
				.then(data => { if (active) setProfile(data as UsersProfileProfile1); })
				.catch(err => console.error('Failed to fetch profile', err));
		} else {
			setProfile(null);
		}
		return () => { active = false; };
	}, [userData]);
	const handleLogout = async (): Promise<void> => {
		try {
			await pca.initialize();
			await pca.logoutPopup();
			if (userData?.session?.session) {
				try {
					await fetchInvalidateToken({ rotationToken: userData.session.session });
				} catch (err) {
					console.error('Failed to invalidate session', err);
				}
			}
			clearUserData();
			setProfile(null);
			setNotification({ open: true, severity: 'info', message: 'Logged out successfully.' });
		} catch (error: any) {
			setNotification({ open: true, severity: 'error', message: `Logout failed: ${error.message}` });
		}
	};

	return (
		<Box sx={{ display: 'flex', alignItems: 'center' }}>
			{userData ? (
				<Tooltip title='Logout'>
					<IconButton onClick={handleLogout}>
						<img src={profile?.profile_image ? `data:image/png;base64,${profile.profile_image}` : ''} alt='user avatar' style={{ width: '28px', height: '28px', borderRadius: '50%', border: '1px solid #000' }} />
					</IconButton>
				</Tooltip>
			) : (
				<Tooltip title='Login'>
					<IconButton onClick={handleLoginNavigation}>
						<LoginIcon />
					</IconButton>
				</Tooltip>
			)}

			{open && (
				<ListItemText
					primary={ userData ? (
						<Box>
							<Typography component={RouterLink} to='/userpage' variant='body1' sx={{fontWeight: 'bold', color: 'gray', textDecoration: 'none' }}>
								{profile?.display_name ?? ''}
							</Typography>
							<Typography component='span' variant='body2' sx={{ display: 'block', fontSize: '0.9em', color: 'gray' }}>
								{profile ? new Intl.NumberFormat(navigator.language).format(profile.credits) : ''}
							</Typography>
						</Box>
					) : (
						'Login'
					)}
					 sx={{ marginLeft: '8px' }}
				/>
			)}

			<Notification
				open={notification.open}
				handleClose={handleNotificationClose}
				severity={notification.severity}
				message={notification.message}
			/>
		</Box>
	);
};

export default Login;
