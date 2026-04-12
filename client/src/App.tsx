import { useEffect, useState } from 'react';

import { Box, CircularProgress, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';

import { loadPath } from './api/rpc';
import { WorkbenchRenderer } from './engine/WorkbenchRenderer';
import type { PathNode } from './engine/types';
import { ElideusTheme } from './theme';
import { UserContextProvider } from './shared/UserContextProvider';

function App(): JSX.Element {
	const [pathData, setPathData] = useState<PathNode | null>(null);
	const [componentData, setComponentData] = useState<Record<string, unknown>>({});
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		loadPath(window.location.pathname)
			.then((result) => {
				setPathData(result.pathData);
				setComponentData(result.componentData);
			})
			.catch((err: unknown) => {
				setError(err instanceof Error ? err.message : 'Failed to load path');
			});
	}, []);

	if (error) {
		return <Box sx={{ p: 4, color: 'error.main' }}>{error}</Box>;
	}

	if (!pathData) {
		return (
			<Box sx={{ p: 4 }}>
				<CircularProgress />
			</Box>
		);
	}

	return (
		<UserContextProvider>
			<ThemeProvider theme={ElideusTheme}>
				<CssBaseline />
				<WorkbenchRenderer pathData={pathData} componentData={componentData} />
			</ThemeProvider>
		</UserContextProvider>
	);
}

export default App;
