import { Box, Typography } from '@mui/material';

interface QueryPreviewPanelProps {
	pageGuid: string | null;
}

export function QueryPreviewPanel({ pageGuid }: QueryPreviewPanelProps): JSX.Element {
	return (
		<Box sx={{ p: 1.5, bgcolor: '#000000', border: '1px solid #1A1A1A' }}>
			<Typography variant="body2">Query derivation available when ContractQueryBuilder is implemented.</Typography>
			<Typography variant="caption" sx={{ color: '#4CAF50' }}>
				Page GUID: {pageGuid ?? 'none'}
			</Typography>
		</Box>
	);
}
