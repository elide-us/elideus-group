import CodeIcon from '@mui/icons-material/Code';
import {
	Box,
	FormControlLabel,
	IconButton,
	Switch,
	Tooltip,
	Typography,
} from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

interface UserLike {
	isAuthenticated?: boolean;
	roles?: string[];
}

export function DevModeToggle({ data }: CmsComponentProps): JSX.Element | null {
	const user = (data.__user ?? null) as UserLike | null;
	const isAuthenticated = user?.isAuthenticated === true;
	const roles = Array.isArray(user?.roles) ? user.roles : [];
	const isServiceAdmin = roles.some((role) => role === 'ROLE_SERVICE_ADMIN');

	if (!isAuthenticated || !isServiceAdmin) {
		return null;
	}

	const isOpen = data.__sidebarOpen === true;
	const isDevMode = data.__devMode === true;
	const toggleDevMode =
		typeof data.__toggleDevMode === 'function' ? (data.__toggleDevMode as () => void) : undefined;

	if (!toggleDevMode) {
		return null;
	}

	if (!isOpen) {
		return (
			<Tooltip title={isDevMode ? 'Disable Dev Mode' : 'Enable Dev Mode'}>
				<IconButton
					onClick={toggleDevMode}
					sx={{
						width: 28,
						height: 28,
						borderRadius: 1,
						color: isDevMode ? '#4CAF50' : '#FFFFFF',
						border: '1px solid #1A1A1A',
						'&:hover': {
							backgroundColor: 'rgba(255, 255, 255, 0.04)',
							borderColor: '#333333',
						},
					}}
				>
					<CodeIcon sx={{ fontSize: 18 }} />
				</IconButton>
			</Tooltip>
		);
	}

	return (
		<Box
			sx={{
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'space-between',
				gap: 1,
			}}
		>
			<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
				<CodeIcon sx={{ fontSize: 18, color: isDevMode ? '#4CAF50' : '#FFFFFF' }} />
				<Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#FFFFFF' }}>
					Dev Mode
				</Typography>
			</Box>
			<FormControlLabel
				label=""
				control={
					<Switch
						checked={isDevMode}
						onChange={toggleDevMode}
						size="small"
						sx={{
							'& .MuiSwitch-switchBase.Mui-checked': {
								color: '#4CAF50',
							},
							'& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
								backgroundColor: '#4CAF50',
								opacity: 0.6,
							},
						}}
					/>
				}
				sx={{ mr: 0 }}
			/>
		</Box>
	);
}
