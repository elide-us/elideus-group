import { useEffect, useMemo, useState } from 'react';
import {
	Box,
	Button,
	Chip,
	Divider,
	IconButton,
	Menu,
	MenuItem,
	Select,
	Switch,
	TextField,
	Typography,
} from '@mui/material';

import {
	deleteComponentProperty,
	deleteTreeNodeProperty,
	type ComponentDetail,
	type ComponentEntry,
	type PropertyCatalogEntry,
	type ResolvedProperty,
	upsertComponentProperty,
	upsertTreeNodeProperty,
} from '../../api/rpc';

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
	propertyCatalog: PropertyCatalogEntry[];
	resolvedProperties: ResolvedProperty[];
	selectedTreeNodeGuid: string | null;
	onSave: (updates: ComponentUpdate) => Promise<void>;
	onPropertyChange: () => Promise<void>;
}

type CategoryKey = 'layout' | 'style' | 'behavior';

const DOT_COLORS: Record<ResolvedProperty['source'], string> = {
	override: '#4CAF50',
	default: '#42A5F5',
	catalog: '#9E9E9E',
};

export function PropertyPanel({
	componentGuid,
	componentDetail,
	components,
	types,
	typeControls,
	propertyCatalog,
	resolvedProperties,
	selectedTreeNodeGuid,
	onSave,
	onPropertyChange,
}: PropertyPanelProps): JSX.Element {
	const [description, setDescription] = useState('');
	const [defaultTypeGuid, setDefaultTypeGuid] = useState<string>('');
	const [categoryOpen, setCategoryOpen] = useState<Record<CategoryKey, boolean>>({
		layout: true,
		style: false,
		behavior: false,
	});
	const [addAnchor, setAddAnchor] = useState<null | HTMLElement>(null);

	const componentEntry = useMemo(
		() => components.find((row) => row.guid === componentGuid) ?? null,
		[components, componentGuid],
	);

	useEffect(() => {
		setDescription(componentDetail?.description ?? componentEntry?.description ?? '');
		setDefaultTypeGuid(componentDetail?.defaultTypeGuid ?? '');
	}, [componentDetail, componentEntry]);

	const isInstanceMode = selectedTreeNodeGuid !== null;
	const activeNodeGuid = selectedTreeNodeGuid ?? resolvedProperties[0]?.nodeGuid ?? null;
	const nodeProps = useMemo(
		() => resolvedProperties.filter((row) => row.nodeGuid === activeNodeGuid),
		[resolvedProperties, activeNodeGuid],
	);
	const byName = useMemo(() => new Map(nodeProps.map((row) => [row.name, row])), [nodeProps]);

	const visibleCatalog = useMemo(() => {
		return propertyCatalog.filter((property) => {
			const resolved = byName.get(property.name);
			if (!resolved) {
				return property.category.toLowerCase() === 'layout';
			}
			return resolved.source !== 'catalog' || property.category.toLowerCase() === 'layout';
		});
	}, [byName, propertyCatalog]);

	const grouped = useMemo(() => {
		const groups: Record<CategoryKey, PropertyCatalogEntry[]> = { layout: [], style: [], behavior: [] };
		for (const item of visibleCatalog) {
			const key = (item.category.toLowerCase() as CategoryKey);
			if (key in groups) {
				groups[key].push(item);
			}
		}
		return groups;
	}, [visibleCatalog]);

	const setPropertyValue = async (property: PropertyCatalogEntry, nextValue: string | null): Promise<void> => {
		if (isInstanceMode && selectedTreeNodeGuid) {
			await upsertTreeNodeProperty({
				treeNodeGuid: selectedTreeNodeGuid,
				propertyGuid: property.guid,
				value: nextValue,
			});
		} else if (componentGuid) {
			await upsertComponentProperty({
				componentGuid,
				propertyGuid: property.guid,
				value: nextValue,
			});
		}
		await onPropertyChange();
	};

	const resetProperty = async (property: PropertyCatalogEntry): Promise<void> => {
		if (isInstanceMode && selectedTreeNodeGuid) {
			await deleteTreeNodeProperty({ treeNodeGuid: selectedTreeNodeGuid, propertyGuid: property.guid });
		} else if (componentGuid) {
			await deleteComponentProperty({ componentGuid, propertyGuid: property.guid });
		}
		await onPropertyChange();
	};

	if (!componentGuid || !componentDetail) {
		return (
			<Box sx={{ width: 280, p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#0A0A0A' }}>
				<Typography variant="body2">Select a component to view its properties.</Typography>
			</Box>
		);
	}

	const addable = propertyCatalog.filter((item) => !byName.has(item.name));

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
			{isInstanceMode ? (
				<Typography variant="caption" sx={{ color: '#BBBBBB' }}>Node: {selectedTreeNodeGuid}</Typography>
			) : null}
			<TextField
				label="Description"
				value={description}
				onChange={(event) => setDescription(event.target.value)}
				multiline
				minRows={2}
				size="small"
				disabled={isInstanceMode}
			/>
			<Select
				size="small"
				value={defaultTypeGuid}
				onChange={(event) => setDefaultTypeGuid(String(event.target.value))}
				disabled={isInstanceMode}
			>
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
			<Divider sx={{ borderColor: '#1A1A1A' }} />
			<Typography variant="caption" sx={{ color: '#4CAF50' }}>
				{isInstanceMode ? 'Instance Overrides' : 'Component Defaults'}
			</Typography>

			{(['layout', 'style', 'behavior'] as CategoryKey[]).map((group) => (
				<Box key={group}>
					<Button
						size="small"
						sx={{ justifyContent: 'flex-start', color: '#CCCCCC' }}
						onClick={() => setCategoryOpen((prev) => ({ ...prev, [group]: !prev[group] }))}
					>
						{categoryOpen[group] ? '▾' : '▸'} {group}
					</Button>
					{categoryOpen[group] ? grouped[group].map((property) => {
						const resolved = byName.get(property.name);
						const source = resolved?.source ?? 'catalog';
						const value = resolved?.value ?? property.defaultValue ?? '';
						const isBool = property.typeName.toUpperCase() === 'BOOL';
						return (
							<Box key={property.guid} sx={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 1, alignItems: 'center', mb: 0.75 }}>
								<Box>
									<Typography variant="body2">{property.name}</Typography>
									<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
										<Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: DOT_COLORS[source] }} />
										<Typography variant="caption" sx={{ color: '#999999' }}>{source}</Typography>
									</Box>
								</Box>
								<Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
									{isBool ? (
										<Switch
											size="small"
											checked={String(value).toLowerCase() === 'true'}
											onChange={(event) => void setPropertyValue(property, event.target.checked ? 'true' : 'false')}
										/>
									) : (
										<TextField
											size="small"
											value={value}
											onChange={(event) => void setPropertyValue(property, event.target.value)}
											sx={{ width: 110 }}
										/>
									)}
									{source === 'override' ? (
										<IconButton size="small" onClick={() => void resetProperty(property)} sx={{ color: '#E57373' }}>×</IconButton>
									) : null}
								</Box>
							</Box>
						);
					}) : null}
				</Box>
			))}

			<Button size="small" variant="outlined" onClick={(event) => setAddAnchor(event.currentTarget)}>
				Add Property
			</Button>
			<Menu anchorEl={addAnchor} open={Boolean(addAnchor)} onClose={() => setAddAnchor(null)}>
				{addable.map((property) => (
					<MenuItem
						key={property.guid}
						onClick={() => {
							setAddAnchor(null);
							void setPropertyValue(property, property.defaultValue);
						}}
					>
						{property.name}
					</MenuItem>
				))}
			</Menu>

			<Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
				GUID: {componentDetail.guid}
			</Typography>
			<Typography variant="caption">Created: {componentDetail.createdOn}</Typography>
			<Typography variant="caption">Modified: {componentDetail.modifiedOn}</Typography>
			<Button
				variant="contained"
				disabled={isInstanceMode}
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
