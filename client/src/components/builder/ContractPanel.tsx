import { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Chip, CircularProgress, Stack, Typography } from '@mui/material';

import { analyzePage, type PageAnalysis } from '../../api/rpc';

interface ContractPanelProps {
	pageGuid: string | null;
}

const SOURCE_COLORS: Record<string, string> = {
	literal: '#2E7D32',
	column: '#1565C0',
	config: '#EF6C00',
	function: '#6A1B9A',
};

export function ContractPanel({ pageGuid }: ContractPanelProps): JSX.Element {
	const [analysis, setAnalysis] = useState<PageAnalysis | null>(null);
	const [loading, setLoading] = useState(false);

	const load = useCallback(async () => {
		if (!pageGuid) {
			setAnalysis(null);
			setLoading(false);
			return;
		}
		setLoading(true);
		try {
			setAnalysis(await analyzePage(pageGuid));
		} catch {
			setAnalysis(null);
		} finally {
			setLoading(false);
		}
	}, [pageGuid]);

	useEffect(() => {
		void load();
	}, [load]);

	const inboundFields = useMemo(() => analysis?.input_model?.fields ?? [], [analysis]);
	const outboundFields = useMemo(() => analysis?.output_model?.fields ?? [], [analysis]);

	return (
		<Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, bgcolor: '#000000' }}>
			<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="subtitle2" sx={{ mb: 1 }}>Inbound Contract</Typography>
				{loading ? (
					<Stack direction="row" spacing={1} alignItems="center">
						<CircularProgress size={14} />
						<Typography variant="body2">Loading…</Typography>
					</Stack>
				) : inboundFields.length > 0 ? (
					<Stack spacing={0.75}>
						{inboundFields.map((field) => (
							<Stack key={field.name} direction="row" spacing={1} justifyContent="space-between">
								<Typography variant="body2">{field.name}</Typography>
								<Typography variant="caption" sx={{ color: '#BDBDBD' }}>
									{field.type}{field.nullable ? ' | nullable' : ''}
								</Typography>
							</Stack>
						))}
					</Stack>
				) : (
					<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
						No input parameters.
					</Typography>
				)}
			</Box>
			<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="subtitle2" sx={{ mb: 1 }}>
					Outbound Contract {analysis?.output_model?.name ? `(${analysis.output_model.name})` : ''}
				</Typography>
				{loading ? (
					<Stack direction="row" spacing={1} alignItems="center">
						<CircularProgress size={14} />
						<Typography variant="body2">Loading…</Typography>
					</Stack>
				) : outboundFields.length > 0 ? (
					<Stack spacing={0.75}>
						{outboundFields.map((field) => (
							<Stack key={`${field.name}-${field.source}`} direction="row" spacing={1} justifyContent="space-between" alignItems="center">
								<Stack>
									<Typography variant="body2">{field.name}</Typography>
									<Typography variant="caption" sx={{ color: '#BDBDBD' }}>
										{field.type}{field.nullable ? ' | nullable' : ''}
									</Typography>
								</Stack>
								<Chip
									size="small"
									label={field.source}
									sx={{
										bgcolor: SOURCE_COLORS[field.source] ?? '#455A64',
										color: '#FFFFFF',
										textTransform: 'capitalize',
									}}
								/>
							</Stack>
						))}
					</Stack>
				) : (
					<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
						No output fields available.
					</Typography>
				)}
			</Box>
		</Box>
	);
}
