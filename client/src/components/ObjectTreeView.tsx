import { useEffect, useState } from 'react';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
	Box,
	CircularProgress,
	IconButton,
	List,
	ListItemButton,
	ListItemIcon,
	ListItemText,
	Typography,
} from '@mui/material';

import {
	readObjectTreeCategories,
	readObjectTreeChildren,
	type ObjectTreeCategory,
	type ObjectTreeColumn,
	type ObjectTreeTable,
} from '../api/rpc';
import { DynamicIcon } from './DynamicIcon';
import type { CmsComponentProps } from '../engine/types';
import type { SelectedNode } from './Workbench';

interface TreeNodeState {
	expanded: boolean;
	loading: boolean;
	children: (ObjectTreeTable | ObjectTreeColumn)[] | null;
	error: string | null;
}

const DEFAULT_NODE_STATE: TreeNodeState = {
	expanded: false,
	loading: false,
	children: null,
	error: null,
};

const getErrorMessage = (error: unknown): string => {
	if (error instanceof Error && error.message.length > 0) {
		return error.message;
	}
	return 'Unable to load children.';
};

const isObjectTreeColumn = (node: ObjectTreeTable | ObjectTreeColumn): node is ObjectTreeColumn =>
	'ordinal' in node;

const getNodeState = (nodeStates: Record<string, TreeNodeState>, guid: string): TreeNodeState =>
	nodeStates[guid] ?? DEFAULT_NODE_STATE;

const sortCategories = (items: ObjectTreeCategory[]): ObjectTreeCategory[] =>
	[...items].sort((a, b) => a.sequence - b.sequence);

const sortTables = (items: ObjectTreeTable[]): ObjectTreeTable[] =>
	[...items].sort((a, b) => a.sequence - b.sequence);

const sortColumns = (items: ObjectTreeColumn[]): ObjectTreeColumn[] =>
	[...items].sort((a, b) => a.ordinal - b.ordinal);

export function ObjectTreeView({ data }: CmsComponentProps): JSX.Element | null {
	const isDevMode = data.__devMode === true;
	const isOpen = data.__sidebarOpen === true;
	const selected = (data.__selectedNode as SelectedNode | null) ?? null;
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [categories, setCategories] = useState<ObjectTreeCategory[]>([]);
	const [categoriesLoading, setCategoriesLoading] = useState(false);
	const [categoriesError, setCategoriesError] = useState<string | null>(null);
	const [nodeStates, setNodeStates] = useState<Record<string, TreeNodeState>>({});

	useEffect(() => {
		if (!isDevMode) {
			return;
		}
		let mounted = true;
		const hydrateCategories = async (): Promise<void> => {
			setCategoriesLoading(true);
			setCategoriesError(null);
			try {
				const response = await readObjectTreeCategories();
				if (!mounted) {
					return;
				}
				setCategories(sortCategories(Array.isArray(response) ? response : []));
			} catch (error) {
				if (mounted) {
					setCategories([]);
					setCategoriesError(getErrorMessage(error));
				}
			} finally {
				if (mounted) {
					setCategoriesLoading(false);
				}
			}
		};

		void hydrateCategories();
		return () => {
			mounted = false;
		};
	}, [isDevMode]);

	if (!isDevMode) {
		return null;
	}

	const toggleNode = async (categoryGuid: string, nodeGuid: string, tableGuid?: string): Promise<void> => {
		const currentState = getNodeState(nodeStates, nodeGuid);
		const shouldExpand = !currentState.expanded;
		if (!shouldExpand) {
			setNodeStates((previous) => ({
				...previous,
				[nodeGuid]: {
					...getNodeState(previous, nodeGuid),
					expanded: false,
				},
			}));
			return;
		}

		if (currentState.children && !currentState.error) {
			setNodeStates((previous) => ({
				...previous,
				[nodeGuid]: {
					...getNodeState(previous, nodeGuid),
					expanded: true,
				},
			}));
			return;
		}

		setNodeStates((previous) => ({
			...previous,
			[nodeGuid]: {
				...getNodeState(previous, nodeGuid),
				expanded: true,
				loading: true,
				error: null,
			},
		}));

		try {
			const response = await readObjectTreeChildren(categoryGuid, tableGuid);
			const children = (Array.isArray(response) ? response : []) as (ObjectTreeTable | ObjectTreeColumn)[];
			const sortedChildren = tableGuid
				? sortColumns(children.filter(isObjectTreeColumn))
				: sortTables(children.filter((child): child is ObjectTreeTable => !isObjectTreeColumn(child)));

			setNodeStates((previous) => ({
				...previous,
				[nodeGuid]: {
					...getNodeState(previous, nodeGuid),
					expanded: true,
					loading: false,
					children: sortedChildren,
					error: null,
				},
			}));
		} catch (error) {
			setNodeStates((previous) => ({
				...previous,
				[nodeGuid]: {
					...getNodeState(previous, nodeGuid),
					expanded: true,
					loading: false,
					children: null,
					error: getErrorMessage(error),
				},
			}));
		}
	};

	const rowSx = (active: boolean, color: string) => ({
		minHeight: 28,
		px: '8px',
		py: '5px',
		borderRadius: 1,
		justifyContent: isOpen ? 'flex-start' : 'center',
		gap: isOpen ? 1 : 0,
		color,
		backgroundColor: active ? 'rgba(76, 175, 80, 0.12)' : 'transparent',
		'&:hover': {
			backgroundColor: active ? 'rgba(76, 175, 80, 0.18)' : 'rgba(255, 255, 255, 0.04)',
			color,
		},
	});

	const renderNodeText = (label: string, color: string): JSX.Element | null =>
		isOpen ? (
			<ListItemText
				primary={label}
				primaryTypographyProps={{
					fontSize: '0.75rem',
					lineHeight: 1.2,
					whiteSpace: 'nowrap',
					overflow: 'hidden',
					textOverflow: 'ellipsis',
					color,
				}}
			/>
		) : null;

	return (
		<Box sx={{ px: 0.5, py: 0.5 }}>
			{isOpen ? (
				<Typography variant="body2" sx={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#555555', px: 1, py: 0.5 }}>
					Object Tree
				</Typography>
			) : null}
			<List sx={{ px: 0, py: 0 }}>
				{categoriesLoading ? (
					<Box sx={{ display: 'flex', justifyContent: isOpen ? 'flex-start' : 'center', px: 1, py: 1 }}>
						<CircularProgress size={14} thickness={5} />
					</Box>
				) : null}
				{categoriesError ? (
					<Box sx={{ display: 'flex', alignItems: 'center', px: 1, py: 0.5, color: '#E57373', gap: 0.5 }}>
						<ErrorOutlineIcon sx={{ fontSize: 14 }} />
						{isOpen ? <Typography sx={{ fontSize: '0.7rem', lineHeight: 1.2, color: 'inherit' }}>{categoriesError}</Typography> : null}
					</Box>
				) : null}
				{categories.map((category) => {
					const categoryState = getNodeState(nodeStates, category.guid);
					const categoryTables = categoryState.children?.filter((child): child is ObjectTreeTable => !isObjectTreeColumn(child));
					const isCategorySelected = selected?.categoryGuid === category.guid && !selected.nodeGuid && !selected.childGuid;

					return (
						<Box key={category.guid}>
							<Box sx={{ display: 'flex', alignItems: 'center' }}>
								<IconButton size="small" onClick={() => void toggleNode(category.guid, category.guid)} sx={{ color: '#FFFFFF', width: 22, height: 22 }}>
									{categoryState.expanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
								</IconButton>
								<ListItemButton
									onClick={() =>
										selectNode?.({
											categoryGuid: category.guid,
											categoryName: category.name,
											nodeGuid: null,
											nodeName: null,
											childGuid: null,
											childName: null,
											builderComponent: category.builderComponent ?? null,
										})
									}
									sx={rowSx(isCategorySelected, '#FFFFFF')}
								>
									<ListItemIcon sx={{ minWidth: 0, width: 18, height: 18, color: 'inherit', justifyContent: 'center', '& .MuiSvgIcon-root': { fontSize: 18 } }}>
										<DynamicIcon name={category.icon} />
									</ListItemIcon>
									{renderNodeText(category.display, '#FFFFFF')}
								</ListItemButton>
							</Box>
							{categoryState.expanded && isOpen ? (
								<Box sx={{ pl: '16px' }}>
									{categoryState.loading ? <Box sx={{ display: 'flex', alignItems: 'center', px: 1, py: 0.5 }}><CircularProgress size={12} thickness={5} /></Box> : null}
									{categoryState.error ? <Box sx={{ display: 'flex', alignItems: 'center', px: 1, py: 0.5, color: '#E57373', gap: 0.5 }}><ErrorOutlineIcon sx={{ fontSize: 14 }} /><Typography sx={{ fontSize: '0.7rem', lineHeight: 1.2, color: 'inherit' }}>{categoryState.error}</Typography></Box> : null}
									{!categoryState.loading && !categoryState.error && Array.isArray(categoryTables) && categoryTables.length === 0 ? <Typography sx={{ fontSize: '0.7rem', color: '#777777', px: 1, py: 0.5 }}>No items</Typography> : null}
									{categoryTables?.map((table) => {
										const tableState = getNodeState(nodeStates, table.guid);
										const tableColumns = tableState.children?.filter(isObjectTreeColumn);
										const isTableSelected = selected?.categoryGuid === category.guid && selected?.nodeGuid === table.guid && !selected?.childGuid;

										return (
											<Box key={table.guid}>
												<Box sx={{ display: 'flex', alignItems: 'center' }}>
													{category.treeDepth >= 2 ? (
														<IconButton size="small" onClick={() => void toggleNode(category.guid, table.guid, table.guid)} sx={{ color: '#BBBBBB', width: 22, height: 22 }}>
															{tableState.expanded ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
														</IconButton>
													) : (
														<Box sx={{ width: 22, height: 22 }} />
													)}
													<ListItemButton
														onClick={() =>
															selectNode?.({
																categoryGuid: category.guid,
																categoryName: category.name,
																nodeGuid: table.guid,
																nodeName: table.name,
																childGuid: null,
																childName: null,
																builderComponent: category.builderComponent ?? null,
															})
														}
														sx={rowSx(isTableSelected, '#BBBBBB')}
													>
														<ListItemIcon sx={{ minWidth: 0, width: 18, height: 18, color: 'inherit', justifyContent: 'center', '& .MuiSvgIcon-root': { fontSize: 18 } }}>
															<DynamicIcon name="DataObject" />
														</ListItemIcon>
														{renderNodeText(table.name, '#BBBBBB')}
													</ListItemButton>
												</Box>
												{category.treeDepth >= 2 && tableState.expanded ? (
													<Box sx={{ pl: '24px' }}>
														{tableColumns?.map((column) => {
															const isColumnSelected =
																selected?.categoryGuid === category.guid && selected?.nodeGuid === table.guid && selected?.childGuid === column.guid;
															return (
																<ListItemButton
																	key={column.guid}
																	onClick={() =>
																		selectNode?.({
																			categoryGuid: category.guid,
																			categoryName: category.name,
																			nodeGuid: table.guid,
																			nodeName: table.name,
																			childGuid: column.guid,
																			childName: column.name,
																			builderComponent: category.builderComponent ?? null,
																		})
																	}
																	sx={rowSx(isColumnSelected, '#888888')}
																>
																	<ListItemIcon sx={{ minWidth: 0, width: 18, height: 18, color: 'inherit', justifyContent: 'center', '& .MuiSvgIcon-root': { fontSize: 18 } }}>
																		<DynamicIcon name="List" />
																	</ListItemIcon>
																	{renderNodeText(column.name, '#888888')}
																</ListItemButton>
															);
														})}
													</Box>
												) : null}
											</Box>
										);
									})}
								</Box>
							) : null}
						</Box>
					);
				})}
			</List>
		</Box>
	);
}
