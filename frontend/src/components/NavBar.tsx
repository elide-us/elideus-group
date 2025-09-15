import { useState, useEffect, useContext, Fragment } from 'react';
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
        Divider,
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
                                {(() => {
                                        const renderItem = (route: PublicLinksNavBarRoute1) => {

                                                const IconComp = iconMap[route.icon ?? ''] || defaultIcon;
                                                return (
                                                        <ListItemButton component={Link} to={route.path} key={route.path}>
                                                                <ListItemIcon>
                                                                        <IconComp />
                                                                </ListItemIcon>
                                                                {open && <ListItemText primary={route.name} />}
                                                        </ListItemButton>
                                                );
                                        };

                                        const renderSection = (
                                                label: string | null,
                                                items: PublicLinksNavBarRoute1[],
                                                key: string,
                                        ) => {
                                                if (!items.length) {
                                                        return null;
                                                }
                                                return (
                                                        <Fragment key={key}>
                                                                {label ? (
                                                                        <Divider
                                                                                component="li"
                                                                                textAlign="left"
                                                                                sx={{
                                                                                        fontSize: '0.55rem',
                                                                                        textTransform: 'uppercase',
                                                                                        my: 0.5,
                                                                                        mx: 1,
                                                                                        '&::before, &::after': {
                                                                                                borderColor: 'divider',
                                                                                        },
                                                                                }}
                                                                        >
                                                                                {open ? label : undefined}
                                                                        </Divider>
                                                                ) : null}
                                                                {items.map(renderItem)}
                                                        </Fragment>
                                                );
                                        };

                                        const normalizeLabel = (value: string | null | undefined) => {
                                                if (!value) {
                                                        return null;
                                                }
                                                const sanitized = value.trim().replace(/[-_]/g, ' ');
                                                const [firstWord] = sanitized.split(/\s+/);
                                                return firstWord ? firstWord.toUpperCase() : null;
                                        };

                                        const getSectionLabel = (items: PublicLinksNavBarRoute1[]) => {
                                                const candidate = items.find(
                                                        (item) => !(item.path === '/' || item.path.startsWith('/gallery')),
                                                );
                                                if (!candidate) {
                                                        return null;
                                                }
                                                const segment = candidate.path.split('/').filter(Boolean)[0];
                                                return normalizeLabel(segment) ?? normalizeLabel(candidate.name);
                                        };

                                        const sections = new Map<number, PublicLinksNavBarRoute1[]>();
                                        const sortedRoutes = [...routes].sort((a, b) => a.sequence - b.sequence);
                                        sortedRoutes.forEach((route) => {
                                                const groupKey = Math.floor(route.sequence / 100) * 100;
                                                const existing = sections.get(groupKey);
                                                if (existing) {
                                                        existing.push(route);
                                                } else {
                                                        sections.set(groupKey, [route]);
                                                }
                                        });

                                        return Array.from(sections.entries())
                                                .sort(([a], [b]) => a - b)
                                                .map(([groupKey, items]) => {
                                                        const sectionItems = [...items].sort((a, b) => a.sequence - b.sequence);
                                                        const label = getSectionLabel(sectionItems);
                                                        return renderSection(label, sectionItems, `${groupKey}-${label ?? 'none'}`);
                                                });
                                })()}
                        </List>
			<Box sx={{ p: 1 }}>
				<Login open={open} />
			</Box>
		</Drawer>
	);
};

export default NavBar;
