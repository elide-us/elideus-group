import { Box, Typography } from '@mui/material';

interface ContractPanelProps {
	pageGuid: string | null;
}

export function ContractPanel({ pageGuid }: ContractPanelProps): JSX.Element {
	return (
		<Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, bgcolor: '#000000' }}>
			<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="subtitle2">Inbound Contract</Typography>
				<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
					Inbound contract preview will appear when contract introspection is implemented.
				</Typography>
			</Box>
			<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="subtitle2">Outbound Contract</Typography>
				<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
					Outbound contract preview will appear when contract introspection is implemented.
				</Typography>
				<Typography variant="caption" sx={{ color: '#4CAF50' }}>
					Context page: {pageGuid ?? 'none'}
				</Typography>
			</Box>
		</Box>
	);
}
