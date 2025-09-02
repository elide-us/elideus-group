import { useState, useContext } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { Login as LoginIcon } from '@mui/icons-material';
import { Typography, Box, Tooltip, IconButton, ListItemText } from '@mui/material';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig } from '../config/msal';
import { fetchInvalidateToken, fetchLogoutDevice } from '../rpc/auth/session';
import Notification from './Notification';
import UserContext from '../shared/UserContext';

const pca = new PublicClientApplication(msalConfig);

interface LoginProps {
	open: boolean;
}

const Login = ({ open }: LoginProps): JSX.Element => {
		const { userData, clearUserData } = useContext(UserContext);
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
		const handleLogout = async (): Promise<void> => {
				try {
						switch (userData?.provider) {
								case 'microsoft':
										await pca.initialize();
										await pca.logoutPopup();
										break;
								case 'google': {
										const oauth2 = (window as any)?.google?.accounts?.oauth2;
										if (oauth2?.revoke) {
												await new Promise(resolve => oauth2.revoke(userData?.sessionToken, () => resolve(null)));
										} else if (oauth2?.disableAutoSelect) {
												oauth2.disableAutoSelect();
										}
										break;
								}
								default:
										// Other providers can be handled here in the future
										break;
						}

						if (userData?.sessionToken) {
								const logoutRes = await fetchLogoutDevice({ token: userData.sessionToken });
								const invalidateRes = await fetchInvalidateToken();
								if (!logoutRes?.ok || !invalidateRes?.ok) {
										throw new Error('Failed to revoke session');
								}
						}

						clearUserData();
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
												<img src={userData?.profile_image ? `data:image/png;base64,${userData.profile_image}` : ''} alt='user avatar' style={{ width: '28px', height: '28px', borderRadius: '50%', border: '1px solid #000' }} />
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
																{userData?.display_name ?? ''}
														</Typography>
														<Typography component='span' variant='body2' sx={{ display: 'block', fontSize: '0.9em', color: 'gray' }}>
																{userData ? new Intl.NumberFormat(navigator.language).format(userData.credits) : ''}
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
