import { Typography } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function LabelElement({ node, data }: CmsComponentProps): JSX.Element {
	const text = node.fieldBinding ? (data[node.fieldBinding] as string) : node.label;

	return (
		<Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
			{text || ''}
		</Typography>
	);
}
