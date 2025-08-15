import { useContext, useState } from 'react';
import { Container, Paper, Typography, Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig, loginRequest } from './config/msal';
import UserContext from './shared/UserContext';
import Notification from './Notification';
import { fetchOauthLogin } from './rpc/auth/microsoft';
import type { AuthTokens } from './shared/RpcModels';

const pca = new PublicClientApplication(msalConfig);

const LoginPage = (): JSX.Element => {
	const { setUserData } = useContext(UserContext);
	const [notification, setNotification] = useState({
		open: false,
		severity: 'info' as 'info' | 'success' | 'warning' | 'error',
		message: ''
	});
	const navigate = useNavigate();

	const handleNotificationClose = (): void => {
		setNotification(prev => ({ ...prev, open: false }));
	};

	const handleMicrosoftLogin = async (): Promise<void> => {
		try {
			await pca.initialize();
			const loginResponse = await pca.loginPopup(loginRequest);
			const { idToken, accessToken } = loginResponse;

			const data = await fetchOauthLogin({
				idToken,
				accessToken,
				provider: 'microsoft',
			}) as AuthTokens;

			setUserData(data);
			setNotification({ open: true, severity: 'success', message: 'Login successful!' });
			navigate('/');
		} catch (error: any) {
			setNotification({ open: true, severity: 'error', message: `Login failed: ${error.message}` });
		}
	};

	return (
		<Container component='main' maxWidth='xs'>
			<Paper elevation={3} sx={{ marginTop: 8, padding: 4 }}>
				<Typography component='h1' variant='h5' align='center'>
					Sign in
				</Typography>
				<Typography variant='body2' align='center' sx={{ mt: 2 }}>
					Only OAuth providers are supported. Please sign in using one of the following services:
					<br />
					Microsoft, Discord, Google, or Apple.
					<br />
					<strong>Note:</strong> Email-only login is not available.
				</Typography>
				<Stack spacing={2} sx={{ mt: 4 }}>
					<Button variant='contained' fullWidth onClick={handleMicrosoftLogin}>
						Sign in with Microsoft
					</Button>
					<Button variant='outlined' fullWidth disabled>
						Sign in with Discord (Coming Soon)
					</Button>
					<Button variant='outlined' fullWidth disabled>
						Sign in with Google (Coming Soon)
					</Button>
					<Button variant='outlined' fullWidth disabled>
						Sign in with Apple (Coming Soon)
					</Button>
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

export default LoginPage;
