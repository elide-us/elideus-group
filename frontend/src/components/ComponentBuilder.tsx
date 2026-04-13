import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Box, IconButton, Paper, Stack, Typography } from '@mui/material';
import { useMemo, useState } from 'react';
import ComponentPreview from './builder/ComponentPreview';
import ContractPanel from './builder/ContractPanel';
import ComponentTreePanel from './builder/ComponentTreePanel';
import PropertyPanel from './builder/PropertyPanel';
import QueryPreviewPanel from './builder/QueryPreviewPanel';
import type { ComponentDefinition, ComponentTreeNode, DataBindingRow } from './builder/types';

export interface ComponentBuilderProps {
	components: ComponentDefinition[];
	initialNodes: ComponentTreeNode[];
	bindings?: DataBindingRow[];
	onSaveNode?: (node: ComponentTreeNode) => Promise<void> | void;
	onDeleteNode?: (nodeGuid: string) => Promise<void> | void;
	onAddChild?: (parentGuid: string | null) => void;
	onMoveNode?: (nodeGuid: string, direction: 'up' | 'down') => void;
}

type SectionKey = 'tree' | 'query' | 'contracts';

const EMPTY_BINDINGS: DataBindingRow[] = [];

function findNode(nodes: ComponentTreeNode[], guid: string | null): ComponentTreeNode | null {
	if (!guid) {
		return null;
	}
	for (const node of nodes) {
		if (node.guid === guid) {
			return node;
		}
		const child = findNode(node.children, guid);
		if (child) {
			return child;
		}
	}
	return null;
}

function updateNode(nodes: ComponentTreeNode[], updatedNode: ComponentTreeNode): ComponentTreeNode[] {
	return nodes.map((node) => {
		if (node.guid === updatedNode.guid) {
			return { ...updatedNode, children: node.children };
		}
		if (node.children.length === 0) {
			return node;
		}
		return { ...node, children: updateNode(node.children, updatedNode) };
	});
}

function CollapsiblePanel({
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
		<Paper variant="outlined" sx={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
			<Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 1.5, py: 1, borderBottom: open ? 1 : 0, borderColor: 'divider' }}>
				<Typography variant="subtitle2">{title}</Typography>
				<IconButton size="small" onClick={onToggle}>
					{open ? <ExpandLessIcon fontSize="inherit" /> : <ExpandMoreIcon fontSize="inherit" />}
				</IconButton>
			</Stack>
			{open ? <Box sx={{ minHeight: 0 }}>{children}</Box> : null}
		</Paper>
	);
}

export function ComponentBuilder({
	components,
	initialNodes,
	bindings = EMPTY_BINDINGS,
	onSaveNode,
	onDeleteNode,
	onAddChild,
	onMoveNode,
}: ComponentBuilderProps): JSX.Element {
	const [nodes, setNodes] = useState(initialNodes);
	const [selectedNodeGuid, setSelectedNodeGuid] = useState<string | null>(initialNodes[0]?.guid ?? null);
	const [openSections, setOpenSections] = useState<Record<SectionKey, boolean>>({ tree: true, query: true, contracts: true });

	const selectedNode = useMemo(() => findNode(nodes, selectedNodeGuid), [nodes, selectedNodeGuid]);

	return (
		<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, height: '100%', minHeight: 680 }}>
			<Box sx={{ display: 'flex', flex: 1, minHeight: 260 }}>
				<ComponentPreview nodes={nodes} selectedNodeGuid={selectedNodeGuid} onSelectNode={setSelectedNodeGuid} onMoveNode={onMoveNode} />
				<PropertyPanel
					node={selectedNode}
					components={components}
					onChangeNode={(updatedNode) => setNodes((previous) => updateNode(previous, updatedNode))}
					onSaveNode={onSaveNode}
					onDeleteNode={onDeleteNode}
				/>
			</Box>

			<CollapsiblePanel title="Component Tree" open={openSections.tree} onToggle={() => setOpenSections((previous) => ({ ...previous, tree: !previous.tree }))}>
				<ComponentTreePanel
					nodes={nodes}
					selectedNodeGuid={selectedNodeGuid}
					onSelectNode={setSelectedNodeGuid}
					onAddChild={onAddChild}
					onDeleteNode={onDeleteNode}
					onMoveNode={onMoveNode}
				/>
			</CollapsiblePanel>

			<CollapsiblePanel title="Query Preview" open={openSections.query} onToggle={() => setOpenSections((previous) => ({ ...previous, query: !previous.query }))}>
				<QueryPreviewPanel />
			</CollapsiblePanel>

			<CollapsiblePanel title="Contracts" open={openSections.contracts} onToggle={() => setOpenSections((previous) => ({ ...previous, contracts: !previous.contracts }))}>
				<Box sx={{ display: 'flex', gap: 1, p: 1 }}>
					<ContractPanel direction="inbound" bindings={bindings} />
					<ContractPanel direction="outbound" bindings={bindings} />
				</Box>
			</CollapsiblePanel>
		</Box>
	);
}

export default ComponentBuilder;
