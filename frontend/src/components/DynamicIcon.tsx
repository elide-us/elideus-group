import { type ElementType, lazy, memo, Suspense, useMemo } from 'react';
import { SvgIcon } from '@mui/material';

interface DynamicIconProps {
	name: string | null | undefined;
}

const iconCache = new Map<string, ElementType>();

function loadIcon(name: string): ElementType {
	const cached = iconCache.get(name);
	if (cached) return cached;

	const LazyIcon = lazy(() =>
		import(
			/* @vite-ignore */
			`@mui/icons-material/${name}`
		).then(
			(mod) => ({ default: mod.default }),
			() => import('@mui/icons-material/Adjust').then((mod) => ({ default: mod.default })),
		),
	);

	iconCache.set(name, LazyIcon);
	return LazyIcon;
}

const FallbackIcon = (): JSX.Element => (
	<SvgIcon sx={{ fontSize: 'inherit', opacity: 0 }}>
		<rect />
	</SvgIcon>
);

const DynamicIcon = memo(({ name }: DynamicIconProps): JSX.Element => {
	const IconComponent = useMemo(() => (name ? loadIcon(name) : null), [name]);

	if (!IconComponent) {
		return <FallbackIcon />;
	}

	return (
		<Suspense fallback={<FallbackIcon />}>
			<IconComponent />
		</Suspense>
	);
});

DynamicIcon.displayName = 'DynamicIcon';

export default DynamicIcon;
