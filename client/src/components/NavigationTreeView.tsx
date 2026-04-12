import { Fragment, useEffect, useMemo, useState } from 'react';
import { Divider, List, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';

import { readNavigation } from '../api/rpc';
import type { NavigationRouteElement } from '../api/rpc';
import { DynamicIcon } from './DynamicIcon';
import type { CmsComponentProps } from '../engine/types';

const getRouteSequence = (route: NavigationRouteElement): number => {
	const raw = route.sequence;
	if (typeof raw === 'number' && Number.isFinite(raw)) {
		return raw;
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

const getUserRoleKey = (user: unknown): string => {
	if (!user || typeof user !== 'object') {
		return 'anon';
	}
	const roles = (user as { roles?: unknown }).roles;
	if (!Array.isArray(roles)) {
		return 'auth';
	}
	const normalized = roles
		.filter((role): role is string => typeof role === 'string' && role.length > 0)
		.map((role) => role.toUpperCase())
		.sort();
	return normalized.join('|');
};

export function NavigationTreeView({ data }: CmsComponentProps): JSX.Element | null {
	const isOpen = data.__sidebarOpen === true;
	const isDevMode = data.__devMode === true;
	const userRoleKey = useMemo(() => getUserRoleKey(data.__user), [data.__user]);
	const [routes, setRoutes] = useState<NavigationRouteElement[]>([]);

	useEffect(() => {
		let mounted = true;
		const hydrateRoutes = async (): Promise<void> => {
			try {
				const response = await readNavigation();
				if (mounted) {
					const elements = Array.isArray(response.elements) ? response.elements : [];
					setRoutes(elements);
				}
			} catch {
				if (mounted) {
					setRoutes([]);
				}
			}
		};

		void hydrateRoutes();
		return () => {
			mounted = false;
		};
	}, [userRoleKey]);

	const pathname = window.location.pathname;
	const sections = useMemo(() => {
		const grouped = new Map<number, NavigationRouteElement[]>();
		const sorted = [...routes].sort((a, b) => getRouteSequence(a) - getRouteSequence(b));
		sorted.forEach((route) => {
			const key = getSectionKey(getRouteSequence(route));
			const existing = grouped.get(key);
			if (existing) {
				existing.push(route);
				return;
			}
			grouped.set(key, [route]);
		});
		return Array.from(grouped.entries()).sort(([a], [b]) => a - b);
	}, [routes]);

	if (isDevMode) {
		return null;
	}

	return (
		<List sx={{ px: 0.5, py: 0 }}>
			{sections.map(([sectionKey, items], index) => (
				<Fragment key={sectionKey}>
					{index > 0 ? <Divider sx={{ borderColor: '#1A1A1A', my: 0.75 }} /> : null}
					{items.map((route) => {
						const active = isRouteActive(pathname, route.path);
						return (
							<ListItemButton
								key={route.path}
								onClick={() => {
									window.location.href = route.path;
								}}
								sx={{
									minHeight: 28,
									px: '8px',
									py: '5px',
									borderRadius: 1,
									justifyContent: isOpen ? 'flex-start' : 'center',
									gap: isOpen ? 1 : 0,
									color: active ? '#4CAF50' : '#FFFFFF',
									backgroundColor: active ? 'rgba(76, 175, 80, 0.12)' : 'transparent',
									'&:hover': {
										backgroundColor: active
											? 'rgba(76, 175, 80, 0.18)'
											: 'rgba(255, 255, 255, 0.04)',
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
									<DynamicIcon name={route.icon} />
								</ListItemIcon>
								{isOpen ? (
									<ListItemText
										primary={route.title}
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
					})}
				</Fragment>
			))}
		</List>
	);
}
