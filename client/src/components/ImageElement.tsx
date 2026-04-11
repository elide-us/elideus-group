import { CardMedia } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function ImageElement({ node, data }: CmsComponentProps): JSX.Element {
	const src = node.fieldBinding ? (data[node.fieldBinding] as string) : null;
	const alt = node.label || '';

	if (!src) {
		return <></>;
	}

	return (
		<CardMedia
			component="img"
			alt={alt}
			image={src}
			sx={{ maxWidth: { xs: '75%', sm: '40%' }, mb: 3 }}
		/>
	);
}
