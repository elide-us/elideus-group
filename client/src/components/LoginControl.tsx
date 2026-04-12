import { useMemo, useState } from 'react';

import { PublicClientApplication } from '@azure/msal-browser';
import LoginIcon from '@mui/icons-material/Login';
import {
	Box,
	Button,
	CircularProgress,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	IconButton,
	ListItemText,
	Tooltip,
	Typography,
} from '@mui/material';

import { getDiscordAuthorizeUrl } from '../config/discord';
import googleConfig from '../config/google';
import { loginRequest, msalConfig } from '../config/msal';
import type { CmsComponentProps } from '../engine/types';
import { getFingerprint } from '../shared/fingerprint';
import Notification from './Notification';

declare global {
	interface Window {
		google?: {
			accounts?: {
				oauth2?: {
					initCodeClient: (config: {
						client_id: string;
						scope: string;
						redirect_uri: string;
						callback: (resp: { code: string }) => void;
					}) => { requestCode: () => void };
				};
			};
		};
	}
}

const pca = new PublicClientApplication(msalConfig);

type LoginFn = (provider: string, tokens: Record<string, unknown>) => Promise<void>;

export function LoginControl({ data }: CmsComponentProps): JSX.Element {
	const user = useMemo(
		() => (data.__user && typeof data.__user === 'object' ? (data.__user as Record<string, unknown>) : null),
		[data.__user],
	);
	const isLoading = data.__isAuthLoading === true;
	const sidebarOpen = data.__sidebarOpen === true;
	const login = typeof data.__login === 'function' ? (data.__login as LoginFn) : null;

	const [dialogOpen, setDialogOpen] = useState<boolean>(false);
	const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
	const [notification, setNotification] = useState({
		open: false,
		severity: 'info' as 'info' | 'success' | 'warning' | 'error',
		message: '',
	});

	const closeNotification = (): void => {
		setNotification((prev) => ({ ...prev, open: false }));
	};

	const handleLoginError = (error: unknown): void => {
		setNotification({
			open: true,
			severity: 'error',
			message: `Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
		});
	};

	const runLogin = async (provider: string, tokens: Record<string, unknown>): Promise<void> => {
		if (!login) {
			throw new Error('Login handler is not available.');
		}
		setIsSubmitting(true);
		try {
			await login(provider, tokens);
			setDialogOpen(false);
			setNotification({
				open: true,
				severity: 'success',
				message: 'Login successful!',
			});
		} catch (error) {
			handleLoginError(error);
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleMicrosoftLogin = async (): Promise<void> => {
		await pca.initialize();
		const loginResponse = await pca.loginPopup(loginRequest);
		await runLogin('microsoft', {
			idToken: loginResponse.idToken,
			id_token: null,
			accessToken: loginResponse.accessToken,
			access_token: null,
			fingerprint: getFingerprint(),
		});
	};

	const handleDiscordLogin = async (): Promise<void> => {
		const authorizeUrl = getDiscordAuthorizeUrl();
		const authWindow = window.open(authorizeUrl, 'discordOAuth', 'width=500,height=600');
		if (!authWindow) {
			throw new Error('Failed to open Discord login window');
		}
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
					// Ignore cross-origin access errors until redirect.
				}
			}, 500);
		});
		await runLogin('discord', { code, fingerprint: getFingerprint() });
	};

	const handleGoogleLogin = async (): Promise<void> => {
		if (!window.google?.accounts?.oauth2) {
			throw new Error('Google API not loaded');
		}
		const code = await new Promise<string>((resolve) => {
			const client = window.google?.accounts?.oauth2?.initCodeClient({
				client_id: googleConfig.clientId,
				scope: googleConfig.scope,
				redirect_uri: googleConfig.redirectUri,
				callback: (resp) => resolve(resp.code),
			});
			client?.requestCode();
		});
		await runLogin('google', { code, fingerprint: getFingerprint() });
	};

	if (isLoading) {
		return (
			<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: sidebarOpen ? 'flex-start' : 'center', p: 0.5 }}>
				<CircularProgress size={18} />
			</Box>
		);
	}

	if (user) {
		return <Box sx={{ minHeight: 32 }} />;
	}

	return (
		<>
			<Box sx={{ display: 'flex', alignItems: 'center', minWidth: 0 }}>
				<Tooltip title="Login">
					<IconButton
						onClick={(): void => setDialogOpen(true)}
						sx={{
							width: 32,
							height: 32,
							color: '#FFFFFF',
							border: '1px solid #1A1A1A',
							borderRadius: 1,
						}}
					>
						<LoginIcon sx={{ fontSize: 18 }} />
					</IconButton>
				</Tooltip>
				{sidebarOpen ? (
					<ListItemText
						primary={<Typography sx={{ fontSize: '0.75rem', color: '#888888' }}>Login</Typography>}
						sx={{ ml: '6px', minWidth: 0 }}
					/>
				) : null}
			</Box>

			<Dialog open={dialogOpen} onClose={(): void => setDialogOpen(false)} fullWidth maxWidth="xs">
				<DialogTitle>Sign in</DialogTitle>
				<DialogContent>
					<Typography variant="body2" sx={{ mb: 2 }}>
						Sign in using Microsoft, Discord, or Google.
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
						<Button variant="contained" loading={isSubmitting} onClick={(): void => void handleMicrosoftLogin()}>
							Sign in with Microsoft
						</Button>
						<Button variant="contained" loading={isSubmitting} onClick={(): void => void handleDiscordLogin()}>
							Sign in with Discord
						</Button>
						<Button variant="contained" loading={isSubmitting} onClick={(): void => void handleGoogleLogin()}>
							Sign in with Google
						</Button>
					</Box>
				</DialogContent>
				<DialogActions>
					<Button onClick={(): void => setDialogOpen(false)}>Cancel</Button>
				</DialogActions>
			</Dialog>

			<Notification
				open={notification.open}
				handleClose={closeNotification}
				severity={notification.severity}
				message={notification.message}
			/>
		</>
	);
}
