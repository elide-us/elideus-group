import { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Breadcrumbs, Typography } from '@mui/material';

import {
	getComponentDetail,
	getPageTree,
	getTypeControls,
	listComponents,
	readObjectTreeChildren,
	type ComponentDetail,
	type ComponentEntry,
	type PageTreeNode,
	upsertComponent,
} from '../api/rpc';
import {
	ComponentPreview,
	ComponentTreePanel,
	ContractPanel,
	PropertyPanel,
	QueryPreviewPanel,
} from './builder';
import type { SelectedNode } from './Workbench';

const TYPES_CATEGORY_GUID = 'EFAB32FE-8DF8-58FD-8C68-39D3B9E3BE00';

interface ComponentBuilderProps {
	data: Record<string, unknown>;
	selected: SelectedNode;
}

interface TypeRow {
	guid: string;
	name: string;
}

function Section({
	title,
	open,
	onToggle,
	children,
}: {
	title: string;
	open: boolean;
	onToggle: () => void;
	children: JSX.Element;
}): JSX.Element {
	return (
		<Box>
			<Box
				onClick={onToggle}
				sx={{
					cursor: 'pointer',
					bgcolor: '#0A0A0A',
					border: '1px solid #1A1A1A',
					px: 1,
					py: 0.75,
					'&:hover': { color: '#4CAF50' },
				}}
			>
				<Typography variant="subtitle2">{open ? '▾' : '▸'} {title}</Typography>
			</Box>
			{open ? <Box sx={{ mt: 1 }}>{children}</Box> : null}
		</Box>
	);
}

export function ComponentBuilder({ data, selected }: ComponentBuilderProps): JSX.Element {
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [componentDetail, setComponentDetail] = useState<ComponentDetail | null>(null);
	const [treeRows, setTreeRows] = useState<PageTreeNode[]>([]);
	const [components, setComponents] = useState<ComponentEntry[]>([]);
	const [types, setTypes] = useState<TypeRow[]>([]);
	const [typeControls, setTypeControls] = useState<{ guid: string; componentName: string; isDefault: boolean }[]>([]);
	const [treeOpen, setTreeOpen] = useState(true);
	const [queryOpen, setQueryOpen] = useState(true);
	const [contractOpen, setContractOpen] = useState(true);
	const [selectedTreeNodeGuid, setSelectedTreeNodeGuid] = useState<string | null>(selected.childGuid ?? null);

	const refreshTree = useCallback(async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setTreeRows([]);
			return;
		}
		try {
			const rows = await getPageTree(selected.nodeGuid);
			setTreeRows(rows);
		} catch {
			setTreeRows([]);
		}
	}, [selected.nodeGuid]);

	const refreshComponentDetail = useCallback(async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setComponentDetail(null);
			setTypeControls([]);
			return;
		}
		try {
			const detail = await getComponentDetail(selected.nodeGuid);
			if (!detail?.guid) {
				setComponentDetail(null);
				setTypeControls([]);
				return;
			}
			setComponentDetail(detail);
			if (detail.defaultTypeGuid) {
				const controls = await getTypeControls(detail.defaultTypeGuid);
				setTypeControls(controls);
			} else {
				setTypeControls([]);
			}
		} catch {
			setComponentDetail(null);
			setTypeControls([]);
		}
	}, [selected.nodeGuid]);

	useEffect(() => {
		void refreshTree();
	}, [refreshTree]);

	useEffect(() => {
		void refreshComponentDetail();
	}, [refreshComponentDetail]);

	useEffect(() => {
		setSelectedTreeNodeGuid(selected.childGuid ?? null);
	}, [selected.childGuid]);

	useEffect(() => {
		let mounted = true;
		const load = async (): Promise<void> => {
			const [componentRows, typeRows] = await Promise.all([
				listComponents(),
				readObjectTreeChildren(TYPES_CATEGORY_GUID),
			]);
			if (!mounted) {
				return;
			}
			setComponents(componentRows);
			setTypes((typeRows as { guid: string; name: string }[]).map((row) => ({ guid: row.guid, name: row.name })));
		};
		void load();
		return () => {
			mounted = false;
		};
	}, []);

	const previewName = useMemo(() => componentDetail?.name ?? selected.nodeName ?? null, [componentDetail, selected.nodeName]);
	const previewCategory = useMemo(() => componentDetail?.category ?? null, [componentDetail]);

	return (
		<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, gap: 1, color: '#FFFFFF', bgcolor: '#000000' }}>
			<Breadcrumbs sx={{ color: '#4CAF50' }}>
				<Typography color="#4CAF50">Components</Typography>
				<Typography color="#4CAF50">{selected.nodeName}</Typography>
			</Breadcrumbs>

			<Box sx={{ display: 'flex', gap: 1, minHeight: 200 }}>
				<ComponentPreview componentName={previewName} componentCategory={previewCategory} treeRows={treeRows} />
				<PropertyPanel
					componentGuid={componentDetail?.guid ?? null}
					componentDetail={componentDetail}
					components={components}
					types={types}
					typeControls={typeControls}
					onSave={async (updates) => {
						await upsertComponent({
							keyGuid: updates.keyGuid,
							description: updates.description,
							defaultTypeGuid: updates.defaultTypeGuid,
						});
						await refreshComponentDetail();
					}}
				/>
			</Box>

			<Section title="Component Tree" open={treeOpen} onToggle={() => setTreeOpen((prev) => !prev)}>
				<ComponentTreePanel
					treeRows={treeRows}
					components={components}
					selectedNodeGuid={selectedTreeNodeGuid}
					pageGuid={selected.nodeGuid}
					onSelectNode={(guid, name) => {
						setSelectedTreeNodeGuid(guid);
						selectNode?.({
							categoryGuid: selected.categoryGuid,
							categoryName: selected.categoryName,
							nodeGuid: selected.nodeGuid,
							nodeName: selected.nodeName,
							childGuid: guid,
							childName: name,
						});
					}}
					onRefreshTree={refreshTree}
				/>
			</Section>

			<Section title="Query Preview" open={queryOpen} onToggle={() => setQueryOpen((prev) => !prev)}>
				<QueryPreviewPanel pageGuid={selected.nodeGuid} />
			</Section>

			<Section title="Contracts" open={contractOpen} onToggle={() => setContractOpen((prev) => !prev)}>
				<ContractPanel pageGuid={selected.nodeGuid} />
			</Section>
		</Box>
	);
}
