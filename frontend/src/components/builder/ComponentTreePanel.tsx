import { Box, IconButton, List, ListItemButton, ListItemText, Stack, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteIcon from '@mui/icons-material/Delete';
import type { ComponentTreeNode } from './types';

export interface ComponentTreePanelProps {
	nodes: ComponentTreeNode[];
	selectedNodeGuid: string | null;
	onSelectNode: (nodeGuid: string) => void;
	onAddChild?: (parentGuid: string | null) => void;
	onDeleteNode?: (nodeGuid: string) => void;
	onMoveNode?: (nodeGuid: string, direction: 'up' | 'down') => void;
}

interface TreeRowProps {
	node: ComponentTreeNode;
	depth: number;
	selectedNodeGuid: string | null;
	onSelectNode: (nodeGuid: string) => void;
	onAddChild?: (parentGuid: string | null) => void;
	onDeleteNode?: (nodeGuid: string) => void;
	onMoveNode?: (nodeGuid: string, direction: 'up' | 'down') => void;
}

function categoryColor(category: ComponentTreeNode['category']): string {
	switch (category) {
		case 'page':
			return '#1976d2';
		case 'section':
			return '#2e7d32';
		default:
			return '#ef6c00';
	}
}

function TreeRow({ node, depth, selectedNodeGuid, onSelectNode, onAddChild, onDeleteNode, onMoveNode }: TreeRowProps): JSX.Element {
	const label = node.pubLabel ?? node.componentName;
	return (
		<>
			<ListItemButton
				selected={selectedNodeGuid === node.guid}
				onClick={() => onSelectNode(node.guid)}
				sx={{
					pl: 1 + depth * 2,
					borderLeft: `3px solid ${categoryColor(node.category)}`,
					mb: 0.5,
					borderRadius: 1,
				}}
			>
				<ListItemText
					primary={label}
					secondary={`${node.componentName} • seq ${node.sequence}`}
					primaryTypographyProps={{ noWrap: true }}
					secondaryTypographyProps={{ noWrap: true }}
				/>
				<Stack direction="row" spacing={0.5}>
					<IconButton size="small" onClick={(event) => { event.stopPropagation(); onMoveNode?.(node.guid, 'up'); }}>
						<ArrowUpwardIcon fontSize="inherit" />
					</IconButton>
					<IconButton size="small" onClick={(event) => { event.stopPropagation(); onMoveNode?.(node.guid, 'down'); }}>
						<ArrowDownwardIcon fontSize="inherit" />
					</IconButton>
					<IconButton size="small" onClick={(event) => { event.stopPropagation(); onAddChild?.(node.guid); }}>
						<AddIcon fontSize="inherit" />
					</IconButton>
					<IconButton size="small" color="error" onClick={(event) => { event.stopPropagation(); onDeleteNode?.(node.guid); }}>
						<DeleteIcon fontSize="inherit" />
					</IconButton>
				</Stack>
			</ListItemButton>
			{node.children.map((child) => (
				<TreeRow
					key={child.guid}
					node={child}
					depth={depth + 1}
					selectedNodeGuid={selectedNodeGuid}
					onSelectNode={onSelectNode}
					onAddChild={onAddChild}
					onDeleteNode={onDeleteNode}
					onMoveNode={onMoveNode}
				/>
			))}
		</>
	);
}

export function ComponentTreePanel(props: ComponentTreePanelProps): JSX.Element {
	const { nodes, selectedNodeGuid, onSelectNode, onAddChild, onDeleteNode, onMoveNode } = props;
	if (nodes.length === 0) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="body2" color="text.secondary">
					No composition tree — this is a leaf component.
				</Typography>
			</Box>
		);
	}
	return (
		<List dense disablePadding>
			{nodes.map((node) => (
				<TreeRow
					key={node.guid}
					node={node}
					depth={0}
					selectedNodeGuid={selectedNodeGuid}
					onSelectNode={onSelectNode}
					onAddChild={onAddChild}
					onDeleteNode={onDeleteNode}
					onMoveNode={onMoveNode}
				/>
			))}
		</List>
	);
}

export default ComponentTreePanel;
