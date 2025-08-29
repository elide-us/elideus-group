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
const SystemRoutesPage = lazy(() => import("./pages/system/SystemRoutesPage"));
const SystemRolesPage = lazy(() => import("./pages/system/SystemRolesPage"));
const FileManager = lazy(() => import("./pages/FileManager"));
const SystemConfigPage = lazy(() => import("./pages/system/SystemConfigPage"));

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
                                                                <Route path="/system-routes" element={<SystemRoutesPage />} />
                                                                <Route path="/system-config" element={<SystemConfigPage />} />
                                                                <Route path="/system-roles" element={<SystemRolesPage />} />
                                                                <Route path="/file-manager" element={<FileManager />} />
                                                        </Routes>
                                                </Suspense>
                                        </Container>
				</Router>
			</UserContextProvider>
		</ThemeProvider>
	);
}

export default App;
