import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { Box, CssBaseline } from '@mui/material';
import { Suspense, lazy } from 'react';
import { ElideusTheme, LAYOUT } from './shared/theme';
import UserContextProvider from './shared/UserContextProvider';
import NavBar from './components/NavBar';

const Home = lazy(() => import('./pages/Home'));
const Gallery = lazy(() => import('./pages/Gallery'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const UserPage = lazy(() => import('./pages/UserPage'));
const ServiceRoutesPage = lazy(() => import('./pages/service/ServiceRoutesPage'));
const ServiceRolesPage = lazy(() => import('./pages/service/ServiceRolesPage'));
const FileManager = lazy(() => import('./pages/FileManager'));
const DiscordPersonasPage = lazy(() => import('./pages/DiscordPersonasPage'));
const DiscordGuildsPage = lazy(() => import('./pages/DiscordGuildsPage'));
const SystemConfigPage = lazy(() => import('./pages/system/SystemConfigPage'));
const SystemModelsPage = lazy(() => import('./pages/system/SystemModelsPage'));
const SystemConversationsPage = lazy(() => import('./pages/system/SystemConversationsPage'));
const SystemBatchJobsPage = lazy(() => import('./pages/system/SystemBatchJobsPage'));
const SystemAsyncTasksPage = lazy(() => import('./pages/system/SystemAsyncTasksPage'));
const FinanceAdminPage = lazy(() => import('./pages/finance/FinanceAdminPage'));
const FinanceAccountantPage = lazy(() => import('./pages/finance/FinanceAccountantPage'));
const FinanceManagerPage = lazy(() => import('./pages/finance/FinanceManagerPage'));
const AccountRolesPage = lazy(() => import('./pages/AccountRolesPage'));
const AccountUsersPage = lazy(() => import('./pages/AccountUsersPage'));
const AccountUserPanel = lazy(() => import('./pages/AccountUserPanel'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const PublicProfile = lazy(() => import('./pages/PublicProfile'));
const TermsOfService = lazy(() => import('./pages/TermsOfService'));

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
									<Route path="/" element={<Home />} />
									<Route path="/gallery" element={<Gallery />} />
									<Route path="/loginpage" element={<LoginPage />} />
									<Route path="/userpage" element={<UserPage />} />
									<Route path="/service-routes" element={<ServiceRoutesPage />} />
									<Route path="/system-config" element={<SystemConfigPage />} />
									<Route path="/system-models" element={<SystemModelsPage />} />
									<Route path="/system-conversations" element={<SystemConversationsPage />} />
									<Route path="/system-batch-jobs" element={<SystemBatchJobsPage />} />
									<Route path="/system-async-tasks" element={<SystemAsyncTasksPage />} />
									<Route path="/finance-admin" element={<FinanceAdminPage />} />
									<Route path="/finance-appr" element={<FinanceManagerPage />} />
									<Route path="/finance-acct" element={<FinanceAccountantPage />} />
									<Route path="/service-roles" element={<ServiceRolesPage />} />
									<Route path="/account-roles" element={<AccountRolesPage />} />
									<Route path="/account-users" element={<AccountUsersPage />} />
									<Route path="/account-users/:guid" element={<AccountUserPanel />} />
									<Route path="/file-manager" element={<FileManager />} />
									<Route path="/discord-personas" element={<DiscordPersonasPage />} />
									<Route path="/discord-guilds" element={<DiscordGuildsPage />} />
									<Route path="/privacy-policy" element={<PrivacyPolicy />} />
									<Route path="/terms-of-service" element={<TermsOfService />} />
									<Route path="/profile/:guid" element={<PublicProfile />} />
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
