import { useState, useEffect } from 'react';
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
import type { RouteItem, AdminLinksRoutes1 } from './shared/RpcModels';
import { fetchRoutes } from './rpc/admin/links';
import { iconMap, defaultIcon } from './icons';

const DRAWER_OPEN = 240;
const DRAWER_CLOSED = 60;

const NavBar = (): JSX.Element => {
	const [open, setOpen] = useState(false);
	const [routes, setRoutes] = useState<RouteItem[]>([]);

	useEffect(() => {
		void (async () => {
			try {
				const res: AdminLinksRoutes1 = await fetchRoutes();
				setRoutes(res.routes);
			} catch {
				setRoutes([]);
			}
		})();
	}, []);

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
				},
			}}
		>
                       <Box sx={{ display: 'flex', justifyContent: 'flex-start', pl: 1, py: 1 }}>
				<Tooltip title="Toggle Menu">
					<IconButton onClick={() => setOpen(!open)}>
						<MenuIcon />
					</IconButton>
				</Tooltip>
			</Box>
			<List sx={{ flexGrow: 1 }}>
				{routes.map((route) => {
					const IconComp = iconMap[route.icon] || defaultIcon;
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
			<Box sx={{ mt: 'auto', p: 1 }}>
				{/* Login component placeholder */}
			</Box>
		</Drawer>
	);
};

export default NavBar;
