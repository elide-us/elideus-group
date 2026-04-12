import { useCallback, useEffect, useState } from 'react';
import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';
import { useUserContext } from '../shared/UserContextProvider';

export function Workbench({ children, enrichData }: CmsComponentProps): JSX.Element {
	const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
	const { user, sessionToken, isLoading, login, logout } = useUserContext();

	const dataEnricher = useCallback(
		(baseData: Record<string, unknown>): Record<string, unknown> => ({
			...baseData,
			__sidebarOpen: sidebarOpen,
			__toggleSidebar: (): void => setSidebarOpen((prev) => !prev),
			__user: user,
			__sessionToken: sessionToken,
			__isAuthLoading: isLoading,
			__login: login,
			__logout: logout,
		}),
		[sidebarOpen, user, sessionToken, isLoading, login, logout],
	);

	useEffect(() => {
		if (typeof enrichData === 'function') {
			(
				enrichData as unknown as (
					enricher: () => (nextData: Record<string, unknown>) => Record<string, unknown>,
				) => void
			)(() => dataEnricher);
		}
	}, [dataEnricher, enrichData]);

	return (
		<Box
			sx={{
				display: 'flex',
				minHeight: '100vh',
				bgcolor: '#000000',
				color: '#FFFFFF',
			}}
		>
			{children}
		</Box>
	);
}
