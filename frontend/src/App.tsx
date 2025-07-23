import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container } from '@mui/material'
import ElideusTheme from './shared/ElideusTheme'
import UserContextProvider from './shared/UserContextProvider'
import Home from './Home'
import NavBar from './NavBar'
import UserPage from './UserPage'
import LoginPage from './LoginPage'
import SystemRoutesPage from './SystemRoutesPage'
import SystemConfigPage from './SystemConfigPage'
import SystemRolesPage from './SystemRolesPage'
import AccountUsersPage from './AccountUsersPage'
import AccountUserPanel from './AccountUserPanel'
import AccountRoleMembersPage from './AccountRoleMembersPage'

function App(): JSX.Element {
	return (
		<ThemeProvider theme={ ElideusTheme }>
			<CssBaseline />
			<UserContextProvider>
				<Router>
					<NavBar />
                                        <Container maxWidth='lg' disableGutters sx={{ bgcolor: 'background.paper', color: 'text.primary', minHeight: '100vh', py: 2 }}>
						<Routes>
							<Route path='/' element={<Home />} />
							<Route path='/userpage' element={<UserPage />} />
							<Route path='/loginpage' element={<LoginPage />} />
							<Route path='/system_routes' element={<SystemRoutesPage />} />
							<Route path='/system_config' element={<SystemConfigPage />} />
							<Route path='/system_roles' element={<SystemRolesPage />} />
							<Route path='/account_userspage' element={<AccountUsersPage />} />
							<Route path='/account_userpanel/:guid' element={<AccountUserPanel />} />
							<Route path='/account_role_members' element={<AccountRoleMembersPage />} />
						</Routes>
					</Container>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
