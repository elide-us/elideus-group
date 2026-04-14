import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent, type WheelEvent } from 'react';
import { Box } from '@mui/material';

import type { PageTreeNode, ResolvedProperty } from '../../api/rpc';

interface ComponentPreviewProps {
	componentName: string | null;
	componentCategory: string | null;
	treeRows: PageTreeNode[];
	resolvedProperties: ResolvedProperty[];
}

interface LayoutNode {
	guid: string;
	componentName: string;
	category: string;
	label: string | null;
	fieldBinding: string | null;
	x: number;
	y: number;
	width: number;
	height: number;
	depth: number;
	isCollapsible: boolean;
	layoutSize: string;
	layoutWidth: number | null;
	children: LayoutNode[];
	groupBoxes: { x: number; y: number; width: number; height: number }[];
}

interface TreeNode {
	guid: string;
	parentGuid: string | null;
	componentName: string;
	category: string;
	label: string | null;
	fieldBinding: string | null;
	sequence: number;
	children: TreeNode[];
}

const CATEGORY_COLORS: Record<string, { fill: string; stroke: string; glow: string }> = {
	page: { fill: '#1565C0', stroke: '#42A5F5', glow: 'rgba(21,101,192,0.4)' },
	section: { fill: '#2E7D32', stroke: '#66BB6A', glow: 'rgba(46,125,50,0.4)' },
	control: { fill: '#E65100', stroke: '#FF9800', glow: 'rgba(230,81,0,0.4)' },
};
const DEFAULT_COLOR = { fill: '#616161', stroke: '#9E9E9E', glow: 'rgba(97,97,97,0.3)' };

const HEADER_HEIGHT = 20;
const CONTAINER_TOP_PADDING = 28;
const CONTAINER_SIDE_PADDING = 6;
const CONTAINER_BOTTOM_PADDING = 6;
const CHILD_GAP = 4;
const LEAF_WIDTH = 120;
const LEAF_HEIGHT = 36;

function getColors(category: string): { fill: string; stroke: string; glow: string } {
	return CATEGORY_COLORS[category] ?? DEFAULT_COLOR;
}

function isContainerCategory(category: string): boolean {
	return category === 'page' || category === 'section';
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number): void {
	const r = Math.min(radius, width / 2, height / 2);
	ctx.beginPath();
	ctx.moveTo(x + r, y);
	ctx.arcTo(x + width, y, x + width, y + height, r);
	ctx.arcTo(x + width, y + height, x, y + height, r);
	ctx.arcTo(x, y + height, x, y, r);
	ctx.arcTo(x, y, x + width, y, r);
	ctx.closePath();
}

function buildTreeRows(treeRows: PageTreeNode[]): TreeNode[] {
	const byGuid = new Map<string, TreeNode>();
	const roots: TreeNode[] = [];

	for (const row of treeRows) {
		byGuid.set(row.guid, {
			guid: row.guid,
			parentGuid: row.parent_guid,
			componentName: row.component_name,
			category: row.component_category,
			label: row.label,
			fieldBinding: row.field_binding,
			sequence: row.sequence,
			children: [],
		});
	}

	for (const node of byGuid.values()) {
		if (node.parentGuid && byGuid.has(node.parentGuid)) {
			byGuid.get(node.parentGuid)?.children.push(node);
		} else {
			roots.push(node);
		}
	}

	const sortTree = (nodes: TreeNode[]): void => {
		nodes.sort((a, b) => a.sequence - b.sequence);
		for (const node of nodes) {
			sortTree(node.children);
		}
	};
	sortTree(roots);

	return roots;
}

function computeLayout(treeRows: PageTreeNode[], propsByNode: Map<string, Map<string, string | null>>): LayoutNode[] {
	const roots = buildTreeRows(treeRows);
	const nodeProp = (guid: string, key: string): string | null | undefined => propsByNode.get(guid)?.get(key);

	const measureNode = (node: TreeNode, depth: number): LayoutNode => {
		const measuredChildren = node.children.map((child) => measureNode(child, depth + 1));
		const isContainer = isContainerCategory(node.category);
		const direction = nodeProp(node.guid, 'layout_direction') === 'row' ? 'row' : 'column';
		const minHeight = Number(nodeProp(node.guid, 'layout_min_height') ?? 0) || 0;
		const layoutSize = nodeProp(node.guid, 'layout_size') ?? 'auto';
		const widthProp = Number(nodeProp(node.guid, 'layout_width') ?? 0) || null;
		const isCollapsible = String(nodeProp(node.guid, 'layout_collapsible') ?? 'false').toLowerCase() === 'true';

		if (!isContainer || measuredChildren.length === 0) {
			return {
				guid: node.guid,
				componentName: node.componentName,
				category: node.category,
				label: node.label,
				fieldBinding: node.fieldBinding,
				x: 0,
				y: 0,
				width: widthProp ?? LEAF_WIDTH,
				height: Math.max(LEAF_HEIGHT, minHeight),
				depth,
				isCollapsible,
				layoutSize,
				layoutWidth: widthProp,
				children: [],
				groupBoxes: [],
			};
		}

		const sizeChild = (children: LayoutNode[], available: number): LayoutNode[] => {
			if (available <= 0) {
				return children;
			}
			const fixed = children
				.filter((child) => child.layoutSize === 'fixed' && child.layoutWidth)
				.reduce((sum, child) => sum + (child.layoutWidth ?? 0), 0);
			const flexChildren = children.filter((child) => child.layoutSize === 'flex');
			const remaining = Math.max(100, available - fixed - (children.length - 1) * CHILD_GAP);
			const flexWidth = flexChildren.length > 0 ? Math.floor(remaining / flexChildren.length) : 0;
			return children.map((child) => ({
				...child,
				width: child.layoutSize === 'fixed' && child.layoutWidth ? child.layoutWidth : child.layoutSize === 'flex' ? flexWidth : child.width,
			}));
		};

		const grouped = new Map<string, LayoutNode[]>();
		for (const child of measuredChildren) {
			const group = nodeProp(child.guid, 'layout_group');
			const key = group && group !== '' ? `g:${group}` : `n:${child.guid}`;
			if (!grouped.has(key)) {
				grouped.set(key, []);
			}
			grouped.get(key)?.push(child);
		}
		const blocks = Array.from(grouped.values());
		const sizedBlocks = blocks.map((block) => sizeChild(block, 520));

		let width = 140;
		let height = CONTAINER_TOP_PADDING + CONTAINER_BOTTOM_PADDING;
		if (direction === 'row') {
			const all = sizedBlocks.flat();
			const totalWidth = all.reduce((sum, child) => sum + child.width, 0) + Math.max(0, all.length - 1) * CHILD_GAP;
			const maxHeight = all.length ? Math.max(...all.map((child) => child.height)) : 0;
			width = Math.max(totalWidth + CONTAINER_SIDE_PADDING * 2, width);
			height += maxHeight;
		} else {
			for (const block of sizedBlocks) {
				if (block.length > 1) {
					const bw = block.reduce((sum, child) => sum + child.width, 0) + (block.length - 1) * CHILD_GAP;
					const bh = Math.max(...block.map((child) => child.height));
					width = Math.max(width, bw + CONTAINER_SIDE_PADDING * 2);
					height += bh + CHILD_GAP;
				} else {
					width = Math.max(width, block[0].width + CONTAINER_SIDE_PADDING * 2);
					height += block[0].height + CHILD_GAP;
				}
			}
			height -= CHILD_GAP;
		}

		return {
			guid: node.guid,
			componentName: node.componentName,
			category: node.category,
			label: node.label,
			fieldBinding: node.fieldBinding,
			x: 0,
			y: 0,
			width: widthProp ?? width,
			height: Math.max(height, 60, minHeight),
			depth,
			isCollapsible,
			layoutSize,
			layoutWidth: widthProp,
			children: sizedBlocks.flat(),
			groupBoxes: [],
		};
	};

	const placeNode = (node: LayoutNode, x: number, y: number): LayoutNode => {
		const direction = nodeProp(node.guid, 'layout_direction') === 'row' ? 'row' : 'column';
		const childrenByGroup = new Map<string, LayoutNode[]>();
		for (const child of node.children) {
			const group = nodeProp(child.guid, 'layout_group');
			const key = group && group !== '' ? `g:${group}` : `n:${child.guid}`;
			if (!childrenByGroup.has(key)) {
				childrenByGroup.set(key, []);
			}
			childrenByGroup.get(key)?.push(child);
		}
		const groups = Array.from(childrenByGroup.values());

		let cursorX = x + CONTAINER_SIDE_PADDING;
		let cursorY = y + CONTAINER_TOP_PADDING;
		const placed: LayoutNode[] = [];
		const groupBoxes: LayoutNode['groupBoxes'] = [];

		for (const group of groups) {
			if (group.length > 1) {
				let gx = direction === 'row' ? cursorX : x + CONTAINER_SIDE_PADDING;
				let gy = cursorY;
				let maxH = 0;
				let totalW = 0;
				for (const child of group) {
					const p = placeNode(child, gx, gy);
					placed.push(p);
					gx += p.width + CHILD_GAP;
					totalW += p.width;
					maxH = Math.max(maxH, p.height);
				}
				groupBoxes.push({ x: direction === 'row' ? cursorX : x + 3, y: cursorY - 2, width: totalW + (group.length - 1) * CHILD_GAP + 6, height: maxH + 4 });
				if (direction === 'row') {
					cursorX += totalW + group.length * CHILD_GAP;
				} else {
					cursorY += maxH + CHILD_GAP;
				}
			} else {
				const child = placeNode(group[0], cursorX, cursorY);
				placed.push(child);
				if (direction === 'row') {
					cursorX += child.width + CHILD_GAP;
				} else {
					cursorY += child.height + CHILD_GAP;
				}
			}
		}

		return { ...node, x, y, children: placed, groupBoxes };
	};

	let rootY = 40;
	return roots.map((root) => {
		const measured = measureNode(root, 0);
		const positioned = placeNode(measured, 40, rootY);
		rootY += positioned.height + 20;
		return positioned;
	});
}

function flattenLayout(nodes: LayoutNode[]): LayoutNode[] {
	const output: LayoutNode[] = [];
	const walk = (node: LayoutNode): void => {
		output.push(node);
		for (const child of node.children) {
			walk(child);
		}
	};
	for (const node of nodes) {
		walk(node);
	}
	return output;
}

export function ComponentPreview({ componentName, componentCategory, treeRows, resolvedProperties }: ComponentPreviewProps): JSX.Element {
	void componentName;
	void componentCategory;

	const canvasRef = useRef<HTMLCanvasElement>(null);
	const layoutRef = useRef<LayoutNode[]>([]);
	const panStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null);
	const [pan, setPan] = useState({ x: 0, y: 0 });
	const [zoom, setZoom] = useState(1);
	const [hoveredGuid, setHoveredGuid] = useState<string | null>(null);
	const [isPanning, setIsPanning] = useState(false);

	const propsByNode = useMemo(() => {
		const map = new Map<string, Map<string, string | null>>();
		for (const rp of resolvedProperties) {
			if (!map.has(rp.nodeGuid)) {
				map.set(rp.nodeGuid, new Map());
			}
			map.get(rp.nodeGuid)?.set(rp.name, rp.value);
		}
		return map;
	}, [resolvedProperties]);

	const allNodes = flattenLayout(layoutRef.current);

	const toWorld = useCallback(
		(screenX: number, screenY: number): { x: number; y: number } => ({
			x: (screenX - pan.x) / zoom,
			y: (screenY - pan.y) / zoom,
		}),
		[pan.x, pan.y, zoom],
	);

	const findNode = useCallback((worldX: number, worldY: number): LayoutNode | null => {
		for (let i = allNodes.length - 1; i >= 0; i -= 1) {
			const node = allNodes[i];
			if (worldX >= node.x && worldX <= node.x + node.width && worldY >= node.y && worldY <= node.y + node.height) {
				return node;
			}
		}
		return null;
	}, [allNodes]);

	const draw = useCallback((): void => {
		const canvas = canvasRef.current;
		if (!canvas) {
			return;
		}
		const ctx = canvas.getContext('2d');
		if (!ctx) {
			return;
		}
		const rect = canvas.getBoundingClientRect();
		const dpr = window.devicePixelRatio || 1;
		const width = Math.max(1, Math.floor(rect.width));
		const height = Math.max(1, Math.floor(rect.height));
		canvas.width = Math.floor(width * dpr);
		canvas.height = Math.floor(height * dpr);

		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx.clearRect(0, 0, width, height);
		ctx.fillStyle = '#0A0A0A';
		ctx.fillRect(0, 0, width, height);

		if (treeRows.length === 0) {
			ctx.fillStyle = '#555555';
			ctx.font = '14px sans-serif';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText('No composition tree', width / 2, height / 2);
			return;
		}

		ctx.save();
		ctx.translate(pan.x, pan.y);
		ctx.scale(zoom, zoom);

		const drawNode = (node: LayoutNode): void => {
			const colors = getColors(node.category);
			const isHovered = hoveredGuid === node.guid;

			for (const box of node.groupBoxes) {
				ctx.save();
				ctx.setLineDash([4, 3]);
				ctx.strokeStyle = 'rgba(180,180,180,0.45)';
				ctx.strokeRect(box.x, box.y, box.width, box.height);
				ctx.restore();
			}

			ctx.save();
			if (isHovered) {
				ctx.shadowColor = colors.glow;
				ctx.shadowBlur = 16;
			}
			roundRect(ctx, node.x, node.y, node.width, node.height, 8);
			ctx.fillStyle = 'rgba(10,10,10,0.9)';
			ctx.fill();
			ctx.lineWidth = 2;
			ctx.strokeStyle = colors.stroke;
			ctx.stroke();
			ctx.restore();

			ctx.save();
			ctx.fillStyle = colors.fill;
			roundRect(ctx, node.x + 1, node.y + 1, node.width - 2, HEADER_HEIGHT, 7);
			ctx.fill();
			ctx.fillStyle = '#FFFFFF';
			ctx.font = 'bold 11px sans-serif';
			ctx.textAlign = 'left';
			ctx.textBaseline = 'middle';
			ctx.fillText(node.componentName, node.x + 8, node.y + HEADER_HEIGHT / 2 + 1);
			if (node.isCollapsible) {
				ctx.fillText('▾', node.x + node.width - 14, node.y + HEADER_HEIGHT / 2 + 1);
			}
			ctx.restore();

			ctx.save();
			ctx.fillStyle = '#4CAF50';
			ctx.font = '9px monospace';
			if (node.layoutSize === 'fixed' && node.layoutWidth) {
				ctx.fillText(`W:${node.layoutWidth}`, node.x + node.width - 42, node.y + node.height - 8);
			}
			if (node.layoutSize === 'flex') {
				ctx.fillText('⇔', node.x + node.width - 18, node.y + node.height - 8);
			}
			ctx.restore();

			for (const child of node.children) {
				drawNode(child);
			}
		};

		for (const node of layoutRef.current) {
			drawNode(node);
		}
		ctx.restore();
	}, [hoveredGuid, pan.x, pan.y, treeRows.length, zoom]);

	useEffect(() => {
		layoutRef.current = computeLayout(treeRows, propsByNode);
		setHoveredGuid(null);
	}, [treeRows, propsByNode]);

	useEffect(() => {
		draw();
	}, [draw, treeRows, resolvedProperties]);

	useEffect(() => {
		const canvas = canvasRef.current;
		if (!canvas) {
			return;
		}
		const observer = new ResizeObserver(() => {
			draw();
		});
		observer.observe(canvas);
		return () => {
			observer.disconnect();
		};
	}, [draw]);

	const handleMouseDown = useCallback((event: MouseEvent<HTMLCanvasElement>): void => {
		const rect = event.currentTarget.getBoundingClientRect();
		const world = toWorld(event.clientX - rect.left, event.clientY - rect.top);
		const targetNode = findNode(world.x, world.y);
		if (targetNode) {
			return;
		}
		panStart.current = { mx: event.clientX, my: event.clientY, px: pan.x, py: pan.y };
		setIsPanning(true);
	}, [findNode, pan.x, pan.y, toWorld]);

	const handleMouseMove = useCallback((event: MouseEvent<HTMLCanvasElement>): void => {
		const rect = event.currentTarget.getBoundingClientRect();
		const screenX = event.clientX - rect.left;
		const screenY = event.clientY - rect.top;
		if (panStart.current) {
			setPan({
				x: panStart.current.px + (event.clientX - panStart.current.mx),
				y: panStart.current.py + (event.clientY - panStart.current.my),
			});
			return;
		}
		const world = toWorld(screenX, screenY);
		const hoveredNode = findNode(world.x, world.y);
		setHoveredGuid((prev) => (prev === hoveredNode?.guid ? prev : hoveredNode?.guid ?? null));
	}, [findNode, toWorld]);

	const handleMouseUp = useCallback((): void => {
		panStart.current = null;
		setIsPanning(false);
	}, []);

	const handleWheel = useCallback((event: WheelEvent<HTMLCanvasElement>): void => {
		event.preventDefault();
		const rect = event.currentTarget.getBoundingClientRect();
		const screenX = event.clientX - rect.left;
		const screenY = event.clientY - rect.top;
		const before = toWorld(screenX, screenY);
		const factor = event.deltaY < 0 ? 1.1 : 0.9;
		const nextZoom = Math.max(0.2, Math.min(4, zoom * factor));
		setZoom(nextZoom);
		setPan({ x: screenX - before.x * nextZoom, y: screenY - before.y * nextZoom });
	}, [toWorld, zoom]);

	return (
		<Box sx={{ flex: 1, minHeight: 200, border: '1px solid #1A1A1A', position: 'relative' }}>
			<canvas
				ref={canvasRef}
				onMouseDown={handleMouseDown}
				onMouseMove={handleMouseMove}
				onMouseUp={handleMouseUp}
				onMouseLeave={handleMouseUp}
				onWheel={handleWheel}
				style={{
					width: '100%',
					height: '100%',
					background: '#0A0A0A',
					cursor: isPanning ? 'grabbing' : 'grab',
					display: 'block',
				}}
			/>
		</Box>
	);
}
