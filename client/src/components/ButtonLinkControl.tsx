import { Button } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function ButtonLinkControl({ node, data }: CmsComponentProps): JSX.Element {
	const url = node.fieldBinding ? String(data[node.fieldBinding] ?? '') : '#';
	const label = node.label ?? 'Link';

	return (
		<Button
			variant="outlined"
			size="small"
			href={url}
			target="_blank"
			rel="noopener noreferrer"
			sx={{ mb: 1 }}
		>
			{label}
		</Button>
	);
}
