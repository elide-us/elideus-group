import { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import {
	Drawer,
	Box,
	IconButton,
	Tooltip,
	List,
	ListItemButton,
	ListItemIcon,
	ListItemText,
} from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import type { PublicLinksNavBarRoute1, PublicLinksNavBarRoutes1 } from '../shared/RpcModels';
import { fetchNavbarRoutes } from '../rpc/public/links';
import { iconMap, defaultIcon } from '../icons';
import UserContext from '../shared/UserContext';
import Login from './Login';

const DRAWER_OPEN = 240;
const DRAWER_CLOSED = 60;

const NavBar = (): JSX.Element => {
	const [open, setOpen] = useState(false);
	const [routes, setRoutes] = useState<PublicLinksNavBarRoute1[]>([]);
	const { userData } = useContext(UserContext);

	useEffect(() => {
		void (async () => {
			try {
				const res: PublicLinksNavBarRoutes1 = await fetchNavbarRoutes();
				setRoutes(res.routes);
			} catch {
				setRoutes([]);
			}
		})();
	}, [userData]);

	return (
		<Drawer
			variant="permanent"
			open={open}
			sx={{
				width: open ? DRAWER_OPEN : DRAWER_CLOSED,
				position: 'fixed',
				height: '100%',
				zIndex: 1300,
				left: (theme) => theme.spacing(3),
				'& .MuiDrawer-paper': {
					width: open ? DRAWER_OPEN : DRAWER_CLOSED,
					overflowX: 'hidden',
					position: 'fixed',
					display: 'flex',
					flexDirection: 'column',
				},
			}}
		>
			<Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', pl: 1, py: 1 }}>
				<Tooltip title="Toggle Menu">
					<IconButton onClick={() => setOpen(!open)}>
						<MenuIcon />
					</IconButton>
				</Tooltip>
			</Box>
			<List sx={{ flexGrow: 1 }}>
				{routes.map((route) => {
					const IconComp = iconMap[route.icon ?? ''] || defaultIcon;
					return (
						<ListItemButton component={Link} to={route.path} key={route.path}>
							<ListItemIcon>
								<IconComp />
							</ListItemIcon>
							{open && <ListItemText primary={route.name} />}
						</ListItemButton>
					);
				})}
			</List>
			<Box sx={{ p: 1 }}>
				<Login open={open} />
			</Box>
		</Drawer>
	);
};

export default NavBar;
