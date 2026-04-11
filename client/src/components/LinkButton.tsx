import { Link as MuiLink } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function LinkButton({ node, data }: CmsComponentProps): JSX.Element {
	const href = node.fieldBinding ? (data[node.fieldBinding] as string) : null;
	const label = node.label || 'Link';
	const isExternal = href?.startsWith('http');

	if (!href) {
		return <></>;
	}

	return (
		<MuiLink
			href={href}
			underline="none"
			target={isExternal ? '_blank' : undefined}
			rel={isExternal ? 'noopener noreferrer' : undefined}
			sx={{
				display: 'block',
				padding: '10px',
				margin: '8px 0',
				borderRadius: '4px',
				transition: 'background 0.3s',
				color: '#ffffff',
				backgroundColor: '#111',
				textDecoration: 'none',
				textAlign: 'center',
				'&:hover': { backgroundColor: '#222' },
			}}
		>
			{label}
		</MuiLink>
	);
}
