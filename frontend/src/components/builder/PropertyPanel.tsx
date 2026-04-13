import { Box, Button, Divider, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import type { ComponentDefinition, ComponentTreeNode } from './types';

export interface PropertyPanelProps {
	node: ComponentTreeNode | null;
	components: ComponentDefinition[];
	onChangeNode: (updated: ComponentTreeNode) => void;
	onSaveNode?: (updated: ComponentTreeNode) => Promise<void> | void;
	onDeleteNode?: (nodeGuid: string) => Promise<void> | void;
}

export function PropertyPanel({ node, components, onChangeNode, onSaveNode, onDeleteNode }: PropertyPanelProps): JSX.Element {
	const [draft, setDraft] = useState<ComponentTreeNode | null>(node);

	useEffect(() => {
		setDraft(node);
	}, [node]);

	const selectedDefinition = useMemo(() => {
		if (!draft) {
			return null;
		}
		return components.find((component) => component.guid === draft.componentGuid) ?? null;
	}, [components, draft]);

	if (!draft) {
		return (
			<Box sx={{ width: 360, p: 2, borderLeft: 1, borderColor: 'divider' }}>
				<Typography variant="body2" color="text.secondary">
					Select a component node to edit properties.
				</Typography>
			</Box>
		);
	}

	const updateDraft = <K extends keyof ComponentTreeNode>(key: K, value: ComponentTreeNode[K]) => {
		const updated = { ...draft, [key]: value };
		setDraft(updated);
		onChangeNode(updated);
	};

	return (
		<Box sx={{ width: 360, p: 2, borderLeft: 1, borderColor: 'divider', overflowY: 'auto' }}>
			<Stack spacing={1.5}>
				<Typography variant="subtitle1">Properties</Typography>
				<TextField
					select
					label="Component type"
					value={draft.componentGuid}
					onChange={(event) => {
						const component = components.find((entry) => entry.guid === event.target.value);
						updateDraft('componentGuid', event.target.value);
						if (component) {
							updateDraft('componentName', component.name);
							updateDraft('category', component.category);
						}
					}}
				>
					{components.map((component) => (
						<MenuItem key={component.guid} value={component.guid}>
							{component.name}
						</MenuItem>
					))}
				</TextField>
				<TextField label="Label" value={draft.pubLabel ?? ''} onChange={(event) => updateDraft('pubLabel', event.target.value)} />
				<TextField label="Field Binding" value={draft.fieldBinding ?? ''} onChange={(event) => updateDraft('fieldBinding', event.target.value)} InputProps={{ sx: { fontFamily: 'monospace' } }} />
				<TextField
					label="Sequence"
					type="number"
					value={draft.sequence}
					onChange={(event) => updateDraft('sequence', Number(event.target.value))}
				/>
				<TextField label="RPC Operation" value={draft.rpcOperation ?? ''} onChange={(event) => updateDraft('rpcOperation', event.target.value)} InputProps={{ sx: { fontFamily: 'monospace' } }} />
				<TextField label="RPC Contract" value={draft.rpcContract ?? ''} onChange={(event) => updateDraft('rpcContract', event.target.value)} InputProps={{ sx: { fontFamily: 'monospace' } }} />
				<Divider />
				<TextField
					label="Default Type"
					value={selectedDefinition?.defaultTypeName ?? selectedDefinition?.refDefaultTypeGuid ?? ''}
					InputProps={{ readOnly: true, sx: { fontFamily: 'monospace' } }}
				/>
				<TextField label="Category" value={selectedDefinition?.category ?? draft.category} InputProps={{ readOnly: true }} />
				<TextField label="GUID" value={draft.guid} InputProps={{ readOnly: true, sx: { fontFamily: 'monospace' } }} />
				<Stack direction="row" spacing={1}>
					<Button variant="contained" onClick={() => onSaveNode?.(draft)}>
						Save
					</Button>
					<Button variant="outlined" color="error" onClick={() => onDeleteNode?.(draft.guid)}>
						Delete
					</Button>
				</Stack>
			</Stack>
		</Box>
	);
}

export default PropertyPanel;
