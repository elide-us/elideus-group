import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, Container } from '@mui/material'
import ElideusTheme from './shared/ElideusTheme'
import UserContextProvider from './shared/UserContextProvider'
import Home from './Home'
import NavBar from './NavBar'
import Gallery from './Gallery'
import LoginPage from './LoginPage'

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
														<Route path='/gallery' element={<Gallery />} />
														<Route path='/loginpage' element={<LoginPage />} />
												</Routes>
					</Container>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
