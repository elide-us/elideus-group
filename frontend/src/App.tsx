import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { Box, CssBaseline } from '@mui/material';
import { Suspense } from 'react';
import { ElideusTheme, LAYOUT } from './shared/theme';
import UserContextProvider from './shared/UserContextProvider';
import NavBar from './components/NavBar';
import PAGE_ROUTES from './routes/registry';

function App(): JSX.Element {
	return (
		<ThemeProvider theme={ElideusTheme}>
			<CssBaseline />
			<UserContextProvider>
				<Router>
					<Box
						sx={{
							display: 'flex',
							minHeight: '100vh',
							bgcolor: 'background.paper',
							color: 'text.primary',
						}}
					>
						<NavBar />
						<Box
							component="main"
							sx={{
								flex: 1,
								minWidth: 0,
								overflowY: 'auto',
								py: `${LAYOUT.PAGE_PADDING_Y}px`,
								px: `${LAYOUT.PAGE_PADDING_X}px`,
							}}
						>
							<Suspense fallback={<div>Loading...</div>}>
								<Routes>
									{PAGE_ROUTES.map((r) => (
										<Route key={r.path} path={r.path} element={<r.component />} />
									))}
								</Routes>
							</Suspense>
						</Box>
					</Box>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
