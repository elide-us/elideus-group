import { useCallback, useEffect, useRef, useState, type MouseEvent, type WheelEvent } from 'react';
import { Box } from '@mui/material';

import type { PageTreeNode } from '../../api/rpc';

interface ComponentPreviewProps {
	componentName: string | null;
	componentCategory: string | null;
	treeRows: PageTreeNode[];
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
	children: LayoutNode[];
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

function computeLayout(treeRows: PageTreeNode[]): LayoutNode[] {
	const roots = buildTreeRows(treeRows);

	const measureNode = (node: TreeNode, depth: number): LayoutNode => {
		const isContainer = isContainerCategory(node.category);
		const measuredChildren = node.children.map((child) => measureNode(child, depth + 1));
		if (!isContainer || measuredChildren.length === 0) {
			if (!isContainer) {
				return {
					guid: node.guid,
					componentName: node.componentName,
					category: node.category,
					label: node.label,
					fieldBinding: node.fieldBinding,
					x: 0,
					y: 0,
					width: LEAF_WIDTH,
					height: LEAF_HEIGHT,
					depth,
					children: [],
				};
			}
			return {
				guid: node.guid,
				componentName: node.componentName,
				category: node.category,
				label: node.label,
				fieldBinding: node.fieldBinding,
				x: 0,
				y: 0,
				width: 140,
				height: 60,
				depth,
				children: [],
			};
		}

		const maxChildWidth = Math.max(...measuredChildren.map((child) => child.width));
		const childrenHeight = measuredChildren.reduce((sum, child) => sum + child.height, 0);
		const gaps = (measuredChildren.length - 1) * CHILD_GAP;
		const width = Math.max(maxChildWidth + CONTAINER_SIDE_PADDING * 2, 140);
		const height = Math.max(childrenHeight + gaps + CONTAINER_TOP_PADDING + CONTAINER_BOTTOM_PADDING, 60);

		return {
			guid: node.guid,
			componentName: node.componentName,
			category: node.category,
			label: node.label,
			fieldBinding: node.fieldBinding,
			x: 0,
			y: 0,
			width,
			height,
			depth,
			children: measuredChildren,
		};
	};

	const placeNode = (node: LayoutNode, x: number, y: number): LayoutNode => {
		let cursorY = y + CONTAINER_TOP_PADDING;
		const positionedChildren = node.children.map((child) => {
			const positioned = placeNode(child, x + CONTAINER_SIDE_PADDING, cursorY);
			cursorY += positioned.height + CHILD_GAP;
			return positioned;
		});
		return {
			...node,
			x,
			y,
			children: positionedChildren,
		};
	};

	let rootY = 40;
	const positionedRoots = roots.map((root) => {
		const measured = measureNode(root, 0);
		const positioned = placeNode(measured, 40, rootY);
		rootY += positioned.height + 20;
		return positioned;
	});

	return positionedRoots;
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

export function ComponentPreview({ componentName, componentCategory, treeRows }: ComponentPreviewProps): JSX.Element {
	void componentName;
	void componentCategory;

	const canvasRef = useRef<HTMLCanvasElement>(null);
	const layoutRef = useRef<LayoutNode[]>([]);
	const panStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null);
	const [pan, setPan] = useState({ x: 0, y: 0 });
	const [zoom, setZoom] = useState(1);
	const [hoveredGuid, setHoveredGuid] = useState<string | null>(null);
	const [isPanning, setIsPanning] = useState(false);

	const allNodes = flattenLayout(layoutRef.current);

	const toWorld = useCallback(
		(screenX: number, screenY: number): { x: number; y: number } => {
			return {
				x: (screenX - pan.x) / zoom,
				y: (screenY - pan.y) / zoom,
			};
		},
		[pan.x, pan.y, zoom],
	);

	const findNode = useCallback(
		(worldX: number, worldY: number): LayoutNode | null => {
			for (let i = allNodes.length - 1; i >= 0; i -= 1) {
				const node = allNodes[i];
				if (worldX >= node.x && worldX <= node.x + node.width && worldY >= node.y && worldY <= node.y + node.height) {
					return node;
				}
			}
			return null;
		},
		[allNodes],
	);

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

			if (isContainerCategory(node.category)) {
				ctx.save();
				ctx.fillStyle = colors.fill;
				roundRect(ctx, node.x + 1, node.y + 1, node.width - 2, HEADER_HEIGHT, 7);
				ctx.fill();
				ctx.fillStyle = '#FFFFFF';
				ctx.font = 'bold 11px sans-serif';
				ctx.textAlign = 'left';
				ctx.textBaseline = 'middle';
				ctx.fillText(node.componentName, node.x + 8, node.y + HEADER_HEIGHT / 2 + 1);
				ctx.restore();
			} else {
				ctx.save();
				ctx.fillStyle = colors.fill;
				ctx.fillRect(node.x + 1, node.y + 1, 4, node.height - 2);
				ctx.fillStyle = '#FFFFFF';
				ctx.font = '11px sans-serif';
				ctx.textAlign = 'left';
				ctx.textBaseline = 'top';
				ctx.fillText(node.componentName, node.x + 10, node.y + 8);
				ctx.fillStyle = '#4CAF50';
				ctx.font = '9px monospace';
				const meta = node.label || node.fieldBinding || '—';
				ctx.fillText(meta, node.x + 10, node.y + 22);
				ctx.restore();
			}

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
		layoutRef.current = computeLayout(treeRows);
		setHoveredGuid(null);
	}, [treeRows]);

	useEffect(() => {
		draw();
	}, [draw, treeRows]);

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
		panStart.current = {
			mx: event.clientX,
			my: event.clientY,
			px: pan.x,
			py: pan.y,
		};
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
		const nextPan = {
			x: screenX - before.x * nextZoom,
			y: screenY - before.y * nextZoom,
		};
		setZoom(nextZoom);
		setPan(nextPan);
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
