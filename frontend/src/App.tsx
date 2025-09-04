import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline, Container } from "@mui/material";
import { Suspense, lazy } from "react";
import ElideusTheme from "./shared/ElideusTheme";
import UserContextProvider from "./shared/UserContextProvider";
import NavBar from "./components/NavBar";
const Home = lazy(() => import("./pages/Home"));
const Gallery = lazy(() => import("./pages/Gallery"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const UserPage = lazy(() => import("./pages/UserPage"));
const ServiceRoutesPage = lazy(() => import("./pages/service/ServiceRoutesPage"));
const ServiceRolesPage = lazy(() => import("./pages/service/ServiceRolesPage"));
const FileManager = lazy(() => import("./pages/FileManager"));
const SystemConfigPage = lazy(() => import("./pages/system/SystemConfigPage"));
const AccountRolesPage = lazy(() => import("./pages/AccountRolesPage"));
const AccountUsersPage = lazy(() => import("./pages/AccountUsersPage"));
const AccountUserPanel = lazy(() => import("./pages/AccountUserPanel"));
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"));

function App(): JSX.Element {
	return (
		<ThemeProvider theme={ElideusTheme}>
			<CssBaseline />
			<UserContextProvider>
				<Router>
					<NavBar />
					<Container
						maxWidth="lg"
						disableGutters
						sx={{
							bgcolor: "background.paper",
							color: "text.primary",
							minHeight: "100vh",
							py: 2,
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
                                                                <Route path="/service-roles" element={<ServiceRolesPage />} />
								<Route path="/account-roles" element={<AccountRolesPage />} />
								<Route path="/account-users" element={<AccountUsersPage />} />
								<Route path="/account-users/:guid" element={<AccountUserPanel />} />
								<Route path="/file-manager" element={<FileManager />} />
								<Route path="/privacy-policy" element={<PrivacyPolicy />} />
							</Routes>
						</Suspense>
					</Container>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
