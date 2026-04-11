import { Container } from '@mui/material';

import type { CmsComponentProps } from '../engine/types';

export function SimplePage({ children }: CmsComponentProps): JSX.Element {
	return (
		<Container
			maxWidth="md"
			sx={{
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				justifyContent: 'center',
				py: 4,
				minHeight: '100%',
			}}
		>
			{children}
		</Container>
	);
}
