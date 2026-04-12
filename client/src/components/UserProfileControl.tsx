import { useMemo, useState } from 'react';

import { Avatar, Box, CircularProgress, IconButton, ListItemText, Tooltip, Typography } from '@mui/material';

import type { UserContext } from '../api/rpc';
import type { CmsComponentProps } from '../engine/types';
import Notification from './Notification';

type LogoutFn = () => Promise<void>;

export function UserProfileControl({ data }: CmsComponentProps): JSX.Element {
	const user = useMemo(() => {
		if (!data.__user || typeof data.__user !== 'object') {
			return null;
		}
		return data.__user as UserContext;
	}, [data.__user]);

	const sidebarOpen = data.__sidebarOpen === true;
	const isLoading = data.__isAuthLoading === true;
	const logout = typeof data.__logout === 'function' ? (data.__logout as LogoutFn) : null;
	const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
	const [notification, setNotification] = useState({
		open: false,
		severity: 'info' as 'info' | 'success' | 'warning' | 'error',
		message: '',
	});

	const closeNotification = (): void => {
		setNotification((prev) => ({ ...prev, open: false }));
	};

	const handleLogout = async (): Promise<void> => {
		if (!logout) {
			return;
		}
		setIsSubmitting(true);
		try {
			await logout();
			setNotification({ open: true, severity: 'info', message: 'Logged out successfully.' });
		} catch (error) {
			setNotification({
				open: true,
				severity: 'error',
				message: `Logout failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
			});
		} finally {
			setIsSubmitting(false);
		}
	};

	if (!user) {
		return <Box sx={{ minHeight: isLoading ? 32 : 0 }} />;
	}

	const secondaryText = user.email || user.roles[0] || 'Authenticated';
	const initials = user.display ? user.display.charAt(0).toUpperCase() : '?';

	return (
		<>
			<Box sx={{ display: 'flex', alignItems: 'center', minWidth: 0 }}>
				<Tooltip title="Logout">
					<IconButton onClick={(): void => void handleLogout()} sx={{ width: 32, height: 32, color: '#FFFFFF' }}>
						{isSubmitting ? (
							<CircularProgress size={18} />
						) : (
							<Avatar
								sx={{
									width: 24,
									height: 24,
									bgcolor: '#1A1A1A',
									color: '#FFFFFF',
									fontSize: '0.75rem',
									border: '1.5px solid #4CAF50',
								}}
							>
								{initials}
							</Avatar>
						)}
					</IconButton>
				</Tooltip>
				{sidebarOpen ? (
					<ListItemText
						primary={
							<Box sx={{ minWidth: 0 }}>
								<Typography
									sx={{
										display: 'block',
										fontSize: '0.7rem',
										lineHeight: 1.2,
										color: '#888888',
										whiteSpace: 'nowrap',
										overflow: 'hidden',
										textOverflow: 'ellipsis',
									}}
								>
									{user.display}
								</Typography>
								<Typography
									sx={{
										display: 'block',
										fontSize: '0.65rem',
										lineHeight: 1.2,
										color: '#555555',
										whiteSpace: 'nowrap',
										overflow: 'hidden',
										textOverflow: 'ellipsis',
									}}
								>
									{secondaryText}
								</Typography>
							</Box>
						}
						sx={{ ml: '6px', minWidth: 0 }}
					/>
				) : null}
			</Box>
			<Notification
				open={notification.open}
				handleClose={closeNotification}
				severity={notification.severity}
				message={notification.message}
			/>
		</>
	);
}
