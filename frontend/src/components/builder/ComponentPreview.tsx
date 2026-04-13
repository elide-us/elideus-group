import { Box, Tooltip, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentTreeNode } from './types';

interface NodeBox {
	nodeGuid: string;
	x: number;
	y: number;
	width: number;
	height: number;
	depth: number;
	label: string;
	category: ComponentTreeNode['category'];
}

export interface ComponentPreviewProps {
	nodes: ComponentTreeNode[];
	selectedNodeGuid: string | null;
	onSelectNode: (nodeGuid: string) => void;
	onMoveNode?: (nodeGuid: string, direction: 'up' | 'down') => void;
}

const CATEGORY_COLORS: Record<ComponentTreeNode['category'], string> = {
	page: '#1976d2',
	section: '#2e7d32',
	control: '#ef6c00',
};

function flattenTree(nodes: ComponentTreeNode[], depth = 0, yOffset = 24, xOffset = 24, rows: NodeBox[] = []): NodeBox[] {
	let cursorY = yOffset;
	for (const node of nodes) {
		const height = 54;
		rows.push({
			nodeGuid: node.guid,
			x: xOffset + depth * 42,
			y: cursorY,
			width: 320 - depth * 12,
			height,
			depth,
			label: node.pubLabel ?? node.componentName,
			category: node.category,
		});
		cursorY += height + 20;
		if (node.children.length > 0) {
			flattenTree(node.children, depth + 1, cursorY, xOffset, rows);
			cursorY = rows[rows.length - 1].y + rows[rows.length - 1].height + 20;
		}
	}
	return rows;
}

export function ComponentPreview({ nodes, selectedNodeGuid, onSelectNode, onMoveNode }: ComponentPreviewProps): JSX.Element {
	const canvasRef = useRef<HTMLCanvasElement | null>(null);
	const wrapperRef = useRef<HTMLDivElement | null>(null);
	const [pan, setPan] = useState({ x: 0, y: 0 });
	const [zoom, setZoom] = useState(1);
	const [hoveredGuid, setHoveredGuid] = useState<string | null>(null);
	const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
	const [isPanning, setIsPanning] = useState(false);
	const [lastPointer, setLastPointer] = useState({ x: 0, y: 0 });

	const boxes = useMemo(() => flattenTree(nodes), [nodes]);

	const draw = useCallback(() => {
		const canvas = canvasRef.current;
		const wrapper = wrapperRef.current;
		if (!canvas || !wrapper) {
			return;
		}
		const dpr = window.devicePixelRatio || 1;
		const width = wrapper.clientWidth;
		const height = wrapper.clientHeight;
		canvas.width = Math.floor(width * dpr);
		canvas.height = Math.floor(height * dpr);
		canvas.style.width = `${width}px`;
		canvas.style.height = `${height}px`;
		const context = canvas.getContext('2d');
		if (!context) {
			return;
		}

		context.setTransform(dpr, 0, 0, dpr, 0, 0);
		context.clearRect(0, 0, width, height);
		context.save();
		context.translate(pan.x, pan.y);
		context.scale(zoom, zoom);

		for (const box of boxes) {
			const color = CATEGORY_COLORS[box.category];
			const isSelected = selectedNodeGuid === box.nodeGuid;
			const isHovered = hoveredGuid === box.nodeGuid;
			context.beginPath();
			context.roundRect(box.x, box.y, box.width, box.height, 10);
			context.fillStyle = `${color}${box.category === 'control' ? 'DD' : 'A6'}`;
			context.fill();
			context.lineWidth = isSelected ? 3 : 1.5;
			context.strokeStyle = isSelected ? '#ffffff' : color;
			context.shadowColor = isHovered ? color : 'transparent';
			context.shadowBlur = isHovered ? 20 : 0;
			context.stroke();
			context.shadowBlur = 0;

			context.fillStyle = '#ffffff';
			context.font = '13px monospace';
			context.fillText(box.label, box.x + 12, box.y + 22);
			context.font = '11px monospace';
			context.fillText(box.category.toUpperCase(), box.x + 12, box.y + 40);
		}

		context.restore();
	}, [boxes, hoveredGuid, pan.x, pan.y, selectedNodeGuid, zoom]);

	useEffect(() => {
		draw();
	}, [draw]);

	const screenToWorld = (screenX: number, screenY: number) => ({
		x: (screenX - pan.x) / zoom,
		y: (screenY - pan.y) / zoom,
	});

	const hitTest = useCallback((clientX: number, clientY: number) => {
		const wrapper = wrapperRef.current;
		if (!wrapper) {
			return null;
		}
		const rect = wrapper.getBoundingClientRect();
		const point = screenToWorld(clientX - rect.left, clientY - rect.top);
		for (const box of boxes) {
			const inX = point.x >= box.x && point.x <= box.x + box.width;
			const inY = point.y >= box.y && point.y <= box.y + box.height;
			if (inX && inY) {
				return box;
			}
		}
		return null;
	}, [boxes, pan.x, pan.y, zoom]);

	return (
		<Box ref={wrapperRef} sx={{ flex: 1, minHeight: 260, position: 'relative', overflow: 'hidden', bgcolor: '#0f1115' }}>
			<canvas
				ref={canvasRef}
				onMouseDown={(event) => {
					setIsPanning(true);
					setLastPointer({ x: event.clientX, y: event.clientY });
				}}
				onMouseUp={(event) => {
					if (isPanning && Math.abs(event.clientX - lastPointer.x) < 2 && Math.abs(event.clientY - lastPointer.y) < 2) {
						const hit = hitTest(event.clientX, event.clientY);
						if (hit) {
							onSelectNode(hit.nodeGuid);
						}
					}
					setIsPanning(false);
				}}
				onMouseMove={(event) => {
					const hit = hitTest(event.clientX, event.clientY);
					setHoveredGuid(hit?.nodeGuid ?? null);
					if (hit) {
						setTooltipPosition({ x: event.nativeEvent.offsetX + 8, y: event.nativeEvent.offsetY + 8 });
					}
					if (isPanning) {
						const deltaX = event.clientX - lastPointer.x;
						const deltaY = event.clientY - lastPointer.y;
						setPan((previous) => ({ x: previous.x + deltaX, y: previous.y + deltaY }));
						setLastPointer({ x: event.clientX, y: event.clientY });
					}
				}}
				onMouseLeave={() => {
					setHoveredGuid(null);
					setIsPanning(false);
				}}
				onWheel={(event) => {
					event.preventDefault();
					const delta = event.deltaY < 0 ? 1.1 : 0.9;
					setZoom((previous) => Math.max(0.4, Math.min(2.2, previous * delta)));
				}}
				onDoubleClick={(event) => {
					const hit = hitTest(event.clientX, event.clientY);
					if (hit) {
						onMoveNode?.(hit.nodeGuid, 'down');
					}
				}}
			/>
			{hoveredGuid ? (
				<Tooltip open title={boxes.find((box) => box.nodeGuid === hoveredGuid)?.label ?? ''} placement="top-start">
					<Typography sx={{ position: 'absolute', left: tooltipPosition.x, top: tooltipPosition.y, pointerEvents: 'none', color: 'transparent' }}>.</Typography>
				</Tooltip>
			) : null}
		</Box>
	);
}

export default ComponentPreview;
