import { useState, useEffect, useContext, Fragment } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
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
import type { PublicLinksNavBarRoute1 } from '../shared/RpcModels';
import { fetchNavbarRoutes } from '../rpc/public/links';
import { iconMap, defaultIcon } from '../icons';
import UserContext from '../shared/UserContext';
import Login from './Login';
import { LAYOUT } from '../shared/theme';

type NavRoute = PublicLinksNavBarRoute1 & {
	sequence?: number | string | null | undefined;
};

const isNavRoute = (value: unknown): value is NavRoute => {
	if (!value || typeof value !== 'object') {
		return false;
	}
	const candidate = value as Record<string, unknown>;
	return typeof candidate.path === 'string' && typeof candidate.name === 'string';
};

const getRouteSequence = (route: NavRoute): number => {
	const raw = route.sequence;
	if (typeof raw === 'number' && Number.isFinite(raw)) {
		return raw;
	}
	if (typeof raw === 'string') {
		const parsed = Number.parseInt(raw, 10);
		if (Number.isFinite(parsed)) {
			return parsed;
		}
	}
	return 0;
};

const getSectionKey = (sequence: number): number => {
	if (!Number.isFinite(sequence)) {
		return 0;
	}
	const bucketStart = Math.floor(sequence / 100) * 100;
	return bucketStart < 0 ? 0 : bucketStart;
};

const isRouteActive = (pathname: string, routePath: string): boolean => {
	if (routePath === '/') {
		return pathname === '/';
	}
	return pathname === routePath || pathname.startsWith(`${routePath}/`);
};

const NavBar = (): JSX.Element => {
	const [open, setOpen] = useState(false);
	const [routes, setRoutes] = useState<NavRoute[]>([]);
	const { userData } = useContext(UserContext);
	const location = useLocation();

	const productsRoute: NavRoute | null = userData
		? { path: '/products', name: 'Products', icon: 'ShoppingCart', sequence: 150 }
		: null;

	const effectiveRoutes = productsRoute
		? [...routes.filter((route) => route.path !== productsRoute.path), productsRoute]
		: routes;

	useEffect(() => {
		void (async () => {
			try {
				const res = await fetchNavbarRoutes();
				const payloadRoutes = Array.isArray(res?.routes)
					? res.routes.filter(isNavRoute)
					: [];
				setRoutes(payloadRoutes);
			} catch {
				setRoutes([]);
			}
		})();
	}, [userData]);

	return (
		<Box
			sx={{
				width: open ? LAYOUT.NAV_WIDTH_EXPANDED : LAYOUT.NAV_WIDTH_COLLAPSED,
				transition: 'width 0.2s ease',
				minHeight: '100vh',
				borderRight: '1px solid #1A1A1A',
				display: 'flex',
				flexDirection: 'column',
				bgcolor: '#000000',
				color: '#FFFFFF',
				flexShrink: 0,
				overflow: 'hidden',
			}}
		>
			<Box
				sx={{
					display: 'flex',
					justifyContent: 'flex-start',
					alignItems: 'center',
					pl: 1,
					py: 1,
				}}
			>
				<Tooltip title="Toggle Menu">
					<IconButton
						onClick={() => setOpen(!open)}
						sx={{
							width: 32,
							height: 32,
							color: '#FFFFFF',
							border: '1px solid #1A1A1A',
							borderRadius: 1,
							'&:hover': {
								borderColor: '#333333',
								backgroundColor: 'rgba(255, 255, 255, 0.04)',
							},
						}}
					>
						<MenuIcon sx={{ fontSize: 18 }} />
					</IconButton>
				</Tooltip>
			</Box>
			<List
				sx={{
					flexGrow: 1,
					overflowX: 'hidden',
					overflowY: 'auto',
					px: 0.5,
					py: 0,
				}}
			>
				{(() => {
					const renderItem = (route: NavRoute) => {
						const IconComp = iconMap[route.icon ?? ''] || defaultIcon;
						const active = isRouteActive(location.pathname, route.path);

						return (
							<ListItemButton
								component={Link}
								to={route.path}
								key={route.path}
								sx={{
									minHeight: 28,
									px: '8px',
									py: '5px',
									borderRadius: 1,
									justifyContent: open ? 'flex-start' : 'center',
									gap: open ? 1 : 0,
									color: active ? '#4CAF50' : '#FFFFFF',
									backgroundColor: active ? 'rgba(76, 175, 80, 0.12)' : 'transparent',
									'&:hover': {
										backgroundColor: active ? 'rgba(76, 175, 80, 0.18)' : 'rgba(255, 255, 255, 0.04)',
										color: active ? '#4CAF50' : '#FFFFFF',
									},
								}}
							>
								<ListItemIcon
									sx={{
										minWidth: 0,
										width: 18,
										height: 18,
										color: 'inherit',
										justifyContent: 'center',
										'& .MuiSvgIcon-root': {
											fontSize: 18,
										},
									}}
								>
									<IconComp />
								</ListItemIcon>
								{open ? (
									<ListItemText
										primary={route.name}
										primaryTypographyProps={{
											fontSize: '0.75rem',
											lineHeight: 1.2,
											whiteSpace: 'nowrap',
											overflow: 'hidden',
											textOverflow: 'ellipsis',
										}}
									/>
								) : null}
							</ListItemButton>
						);
					};

					const renderSection = (
						label: string | null,
						items: NavRoute[],
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
											fontSize: '8px',
											textTransform: 'uppercase',
											letterSpacing: '0.06em',
											color: '#555555',
											my: 0.75,
											mx: open ? 1 : 0.5,
											'&::before, &::after': {
												borderColor: '#1A1A1A',
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

					const getSectionLabel = (items: NavRoute[]) => {
						const candidate = items.find(
							(item) => !(item.path === '/' || item.path.startsWith('/gallery')),
						);
						if (!candidate) {
							return null;
						}
						const segment = candidate.path.split('/').filter(Boolean)[0];
						return normalizeLabel(segment) ?? normalizeLabel(candidate.name);
					};

					const sections = new Map<number, NavRoute[]>();
					const sortedRoutes = [...effectiveRoutes].sort(
						(a, b) => getRouteSequence(a) - getRouteSequence(b),
					);
					sortedRoutes.forEach((route) => {
						const groupKey = getSectionKey(getRouteSequence(route));
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
							const sectionItems = [...items].sort(
								(a, b) => getRouteSequence(a) - getRouteSequence(b),
							);
							const label = groupKey >= 100 ? getSectionLabel(sectionItems) : null;
							return renderSection(label, sectionItems, `${groupKey}-${label ?? 'none'}`);
						});
				})()}
			</List>
			<Box sx={{ p: 1, borderTop: '1px solid #1A1A1A' }}>
				<Login open={open} />
			</Box>
		</Box>
	);
};

export default NavBar;
