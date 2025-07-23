import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container } from '@mui/material'
import ElideusTheme from './shared/ElideusTheme'
import UserContextProvider from './shared/UserContextProvider'
import Home from './Home'
import NavBar from './NavBar'
import LoginPage from './LoginPage'
import UserPage from './UserPage'
import AdminUsersPage from './AdminUsersPage'
import AdminUserPanel from './AdminUserPanel'
import SystemRolesPage from './SystemRolesPage'
import SystemRoleMembersPage from './SystemRoleMembersPage'
import SystemRoutesPage from './SystemRoutesPage'
import SystemConfigPage from './SystemConfigPage'

function App(): JSX.Element {
	return (
		<ThemeProvider theme={ ElideusTheme }>
			<CssBaseline />
			<UserContextProvider>
				<Router>
					<NavBar />
					<Container sx={{ width: '100%', display: 'block', bgcolor: 'background.paper', color: 'text.primary', minHeight: '100vh' }}>
						<Routes>
							<Route path='/' element={<Home />} />
							<Route path='/login' element={<LoginPage />} />
							<Route path='/userpanel' element={<UserPage />} />
							<Route path='/admin_userpanel' element={<AdminUsersPage />} />
							<Route path='/admin_userpanel/:guid' element={<AdminUserPanel />} />
							<Route path='/system_roles' element={<SystemRolesPage />} />
							<Route path='/system_role_members' element={<SystemRoleMembersPage />} />
							<Route path='/system_routes' element={<SystemRoutesPage />} />
							<Route path='/system_config' element={<SystemConfigPage />} />
						</Routes>
					</Container>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
