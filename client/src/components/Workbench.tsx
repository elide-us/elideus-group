import { useCallback, useEffect, useState } from 'react';
import { Box } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function Workbench({ children, enrichData }: CmsComponentProps): JSX.Element {
	const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

	const dataEnricher = useCallback(
		(baseData: Record<string, unknown>): Record<string, unknown> => ({
			...baseData,
			__sidebarOpen: sidebarOpen,
			__toggleSidebar: (): void => setSidebarOpen((prev) => !prev),
		}),
		[sidebarOpen],
	);

	useEffect(() => {
		if (typeof enrichData === 'function') {
			(
				enrichData as unknown as (
					enricher: (nextData: Record<string, unknown>) => Record<string, unknown>,
				) => void
			)(dataEnricher);
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
