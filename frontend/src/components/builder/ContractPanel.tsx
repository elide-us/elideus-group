import { Box, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import type { DataBindingRow } from './types';

export interface ContractPanelProps {
	direction: 'inbound' | 'outbound';
	bindings: DataBindingRow[];
}

export function ContractPanel({ direction, bindings }: ContractPanelProps): JSX.Element {
	return (
		<Paper variant="outlined" sx={{ p: 2, flex: 1, minHeight: 180 }}>
			<Typography variant="subtitle2" gutterBottom>
				{direction === 'inbound' ? 'Inbound Contract' : 'Outbound Contract'}
			</Typography>
			{bindings.length === 0 ? (
				<Box sx={{ color: 'text.secondary' }}>No data binding rows yet.</Box>
			) : (
				<Table size="small">
					<TableHead>
						<TableRow>
							<TableCell>Source</TableCell>
							<TableCell>Alias</TableCell>
							<TableCell>Value</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{bindings.map((binding) => (
							<TableRow key={binding.guid}>
								<TableCell>{binding.sourceType}</TableCell>
								<TableCell sx={{ fontFamily: 'monospace' }}>{binding.alias}</TableCell>
								<TableCell sx={{ fontFamily: 'monospace' }}>{binding.value}</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
			)}
		</Paper>
	);
}

export default ContractPanel;
