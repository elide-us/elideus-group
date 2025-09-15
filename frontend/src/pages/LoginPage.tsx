import { useContext, useState } from 'react';
import { Container, Paper, Typography, Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { PublicClientApplication } from '@azure/msal-browser';
import { msalConfig, loginRequest } from '../config/msal';
import googleConfig from '../config/google';
import { getDiscordAuthorizeUrl } from '../config/discord';
import UserContext from '../shared/UserContext';
import Notification from '../components/Notification';
import { fetchOauthLogin as fetchMicrosoftOauthLogin } from '../rpc/auth/microsoft';
import { fetchOauthLogin as fetchGoogleOauthLogin } from '../rpc/auth/google';
import { fetchOauthLogin as fetchDiscordOauthLogin } from '../rpc/auth/discord';
import { getFingerprint } from '../shared/fingerprint';
import type {
        AuthMicrosoftOauthLogin1,
        AuthGoogleOauthLogin1,
        AuthDiscordOauthLogin1,
} from '../shared/RpcModels';

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
                        console.debug('[LoginPage] Microsoft token data', { idToken, accessToken, account: loginResponse.account, uniqueId: loginResponse.uniqueId });
                        const data = await fetchMicrosoftOauthLogin({
                                idToken,
                                accessToken,
                                provider: 'microsoft',
                                fingerprint: getFingerprint(),
                        }) as AuthMicrosoftOauthLogin1;
                        setUserData({ provider: 'microsoft', ...data });
                        setNotification({ open: true, severity: 'success', message: 'Login successful!' });
                        navigate('/');
                } catch (error: any) {
                        setNotification({ open: true, severity: 'error', message: `Login failed: ${error.message}` });
                }
        };

        const handleDiscordLogin = async (): Promise<void> => {
                try {
                        const authorizeUrl = getDiscordAuthorizeUrl();
                        const authWindow = window.open(authorizeUrl, 'discordOAuth', 'width=500,height=600');
                        if (!authWindow) throw new Error('Failed to open Discord login window');
                        const code = await new Promise<string>((resolve, reject) => {
                                const interval = setInterval(() => {
                                        if (authWindow.closed) {
                                                clearInterval(interval);
                                                reject(new Error('Login window closed'));
                                                return;
                                        }
                                        try {
                                                const url = new URL(authWindow.location.href);
                                                if (url.origin === window.location.origin) {
                                                        const codeParam = url.searchParams.get('code');
                                                        if (codeParam) {
                                                                clearInterval(interval);
                                                                authWindow.close();
                                                                resolve(codeParam);
                                                        }
                                                }
                                        } catch {
                                                // Ignore cross-origin access errors until redirect
                                        }
                                }, 500);
                        });
                        console.debug('[LoginPage] authorization code received', code);
                        const data = await fetchDiscordOauthLogin({
                                code,
                                provider: 'discord',
                                fingerprint: getFingerprint(),
                        }) as AuthDiscordOauthLogin1;
                        setUserData({ provider: 'discord', ...data });
                        setNotification({ open: true, severity: 'success', message: 'Login successful!' });
                        navigate('/');
                } catch (error: any) {
                        setNotification({ open: true, severity: 'error', message: `Login failed: ${error.message}` });
                }
        };

        const handleGoogleLogin = async (): Promise<void> => {
                try {
                        if (!window.google) throw new Error('Google API not loaded');
                        const code = await new Promise<string>((resolve) => {
                                const codeClientConfig = {
                                        client_id: googleConfig.clientId,
                                        scope: googleConfig.scope,
                                        redirect_uri: googleConfig.redirectUri,
                                        callback: (resp: any) => resolve(resp.code),
                                };
                                console.debug('[LoginPage] initCodeClient config', codeClientConfig);
                                const client = window.google.accounts.oauth2.initCodeClient(codeClientConfig);
                                client.requestCode();
                        });
                        console.debug('[LoginPage] authorization code received', code);
                        const data = await fetchGoogleOauthLogin({
                                code,
                                provider: 'google',
                                fingerprint: getFingerprint(),
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
                                        Only OAuth providers are supported. Please sign in using Microsoft, Discord, or Google.
                                        <br />
                                        Apple support is coming soon.
                                        <br />
                                        <strong>Note:</strong> Email-only login is not available.
                                </Typography>
                                <Stack spacing={2} sx={{ mt: 4 }}>
                                        <Button variant='contained' fullWidth onClick={handleMicrosoftLogin}>
                                                Sign in with Microsoft
                                        </Button>
                                       <Button variant='contained' fullWidth onClick={handleDiscordLogin}>
                                               Sign in with Discord
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
