import { Box, Paper, Typography } from '@mui/material';

export function QueryPreviewPanel(): JSX.Element {
	return (
		<Paper variant="outlined" sx={{ p: 2, minHeight: 120 }}>
			<Typography variant="subtitle2" gutterBottom>
				Query Preview
			</Typography>
			<Box sx={{ fontFamily: 'monospace', color: 'text.secondary', whiteSpace: 'pre-wrap' }}>
				Query derivation available when ContractQueryBuilder is implemented.
			</Box>
		</Paper>
	);
}

export default QueryPreviewPanel;
