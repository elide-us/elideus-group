import { useContext, useState } from 'react';
import { Container, Paper, Typography, Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig, loginRequest } from './config/msal';
import googleConfig from './config/google';
import UserContext from './shared/UserContext';
import Notification from './Notification';
import { fetchOauthLogin as fetchMicrosoftOauthLogin } from './rpc/auth/microsoft';
import { fetchOauthLogin as fetchGoogleOauthLogin } from './rpc/auth/google';
import type { AuthMicrosoftOauthLogin1, AuthGoogleOauthLogin1 } from './shared/RpcModels';

declare global {
interface Window {
google: any;
}
}

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
const data = await fetchMicrosoftOauthLogin({
idToken,
accessToken,
provider: 'microsoft',
}) as AuthMicrosoftOauthLogin1;
setUserData({ provider: 'microsoft', ...data });
setNotification({ open: true, severity: 'success', message: 'Login successful!' });
navigate('/');
} catch (error: any) {
setNotification({ open: true, severity: 'error', message: `Login failed: ${error.message}` });
}
};

const handleGoogleLogin = async (): Promise<void> => {
try {
if (!window.google) throw new Error('Google API not loaded');
const accessToken = await new Promise<string>((resolve) => {
const client = window.google.accounts.oauth2.initTokenClient({
client_id: googleConfig.clientId,
scope: googleConfig.scope,
callback: (resp: any) => resolve(resp.access_token),
});
client.requestAccessToken({ prompt: 'consent' });
});
const idToken = await new Promise<string>((resolve) => {
window.google.accounts.id.initialize({
client_id: googleConfig.clientId,
callback: (resp: any) => resolve(resp.credential),
});
window.google.accounts.id.prompt();
});
const data = await fetchGoogleOauthLogin({
idToken,
accessToken,
provider: 'google',
}) as AuthGoogleOauthLogin1;
setUserData({ provider: 'google', ...data });
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
					<Button variant='contained' fullWidth onClick={handleGoogleLogin}>
						Sign in with Google
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
