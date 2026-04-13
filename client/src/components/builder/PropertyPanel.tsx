import { useEffect, useMemo, useState } from 'react';
import { Box, Button, Chip, MenuItem, Select, TextField, Typography } from '@mui/material';

import type { ComponentDetail, ComponentEntry } from '../../api/rpc';

interface TypeRow {
	guid: string;
	name: string;
}

interface ComponentUpdate {
	keyGuid: string;
	name?: string;
	category?: string;
	description?: string | null;
	defaultTypeGuid?: string | null;
}

interface PropertyPanelProps {
	componentGuid: string | null;
	componentDetail: ComponentDetail | null;
	components: ComponentEntry[];
	types: TypeRow[];
	typeControls: { guid: string; componentName: string; isDefault: boolean }[];
	onSave: (updates: ComponentUpdate) => Promise<void>;
}

export function PropertyPanel({
	componentGuid,
	componentDetail,
	components,
	types,
	typeControls,
	onSave,
}: PropertyPanelProps): JSX.Element {
	const [description, setDescription] = useState('');
	const [defaultTypeGuid, setDefaultTypeGuid] = useState<string>('');

	const componentEntry = useMemo(
		() => components.find((row) => row.guid === componentGuid) ?? null,
		[components, componentGuid],
	);

	useEffect(() => {
		setDescription(componentDetail?.description ?? componentEntry?.description ?? '');
		setDefaultTypeGuid(componentDetail?.defaultTypeGuid ?? '');
	}, [componentDetail, componentEntry]);

	if (!componentGuid || !componentDetail) {
		return (
			<Box sx={{ width: 280, p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="body2">Select a component to view its properties.</Typography>
			</Box>
		);
	}

	return (
		<Box
			sx={{
				width: 280,
				p: 1.5,
				display: 'flex',
				flexDirection: 'column',
				gap: 1,
				border: '1px solid #1A1A1A',
				bgcolor: '#0A0A0A',
			}}
		>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
				<Typography variant="subtitle1" noWrap>
					{componentDetail.name}
				</Typography>
				<Chip label={componentDetail.category} size="small" sx={{ bgcolor: '#1A1A1A', color: '#4CAF50' }} />
			</Box>
			<TextField
				label="Description"
				value={description}
				onChange={(event) => setDescription(event.target.value)}
				multiline
				minRows={2}
				size="small"
			/>
			<Select size="small" value={defaultTypeGuid} onChange={(event) => setDefaultTypeGuid(String(event.target.value))}>
				<MenuItem value="">(No default type)</MenuItem>
				{types.map((type) => (
					<MenuItem key={type.guid} value={type.guid}>
						{type.name}
					</MenuItem>
				))}
			</Select>
			<Box sx={{ border: '1px solid #1A1A1A', p: 1, bgcolor: '#000000' }}>
				<Typography variant="caption" sx={{ color: '#4CAF50' }}>
					Type Controls
				</Typography>
				{typeControls.length === 0 ? (
					<Typography variant="body2">No controls mapped.</Typography>
				) : (
					typeControls.map((control) => (
						<Box key={control.guid} sx={{ display: 'flex', justifyContent: 'space-between' }}>
							<Typography variant="body2">{control.componentName}</Typography>
							{control.isDefault ? <Chip size="small" label="default" sx={{ height: 18 }} /> : null}
						</Box>
					))
				)}
			</Box>
			<Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
				GUID: {componentDetail.guid}
			</Typography>
			<Typography variant="caption">Created: {componentDetail.createdOn}</Typography>
			<Typography variant="caption">Modified: {componentDetail.modifiedOn}</Typography>
			<Button
				variant="contained"
				onClick={() =>
					void onSave({
						keyGuid: componentDetail.guid,
						description,
						defaultTypeGuid: defaultTypeGuid || null,
					})
				}
			>
				Save
			</Button>
		</Box>
	);
}
