import { useEffect, useRef, useState, useCallback, type MouseEvent } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import PageTitle from '../../components/PageTitle';
import { fetchFullSchema } from '../../rpc/service/reflection';

interface TableDef {
    recid: number;
    name: string;
}

interface FKDef {
    from: number;
    to: number;
    col: string;
}

interface DomainColor {
    fill: string;
    stroke: string;
    glow: string;
}

const PALETTE: DomainColor[] = [
    { fill: '#4CAF50', stroke: '#81C784', glow: 'rgba(76,175,80,0.5)' },
    { fill: '#BF8C2C', stroke: '#D4A845', glow: 'rgba(191,140,44,0.5)' },
    { fill: '#1565C0', stroke: '#42A5F5', glow: 'rgba(21,101,192,0.4)' },
    { fill: '#00838F', stroke: '#26C6DA', glow: 'rgba(0,131,143,0.4)' },
    { fill: '#5865F2', stroke: '#7983F5', glow: 'rgba(88,101,242,0.4)' },
    { fill: '#6A1B9A', stroke: '#AB47BC', glow: 'rgba(106,27,154,0.4)' },
    { fill: '#546E7A', stroke: '#90A4AE', glow: 'rgba(84,110,122,0.3)' },
    { fill: '#C62828', stroke: '#EF5350', glow: 'rgba(198,40,40,0.4)' },
    { fill: '#2E7D32', stroke: '#66BB6A', glow: 'rgba(46,125,50,0.4)' },
    { fill: '#E65100', stroke: '#FF9800', glow: 'rgba(230,81,0,0.4)' },
    { fill: '#1B5E20', stroke: '#43A047', glow: 'rgba(27,94,32,0.35)' },
    { fill: '#4527A0', stroke: '#7E57C2', glow: 'rgba(69,39,160,0.4)' },
    { fill: '#00695C', stroke: '#26A69A', glow: 'rgba(0,105,92,0.4)' },
    { fill: '#AD1457', stroke: '#EC407A', glow: 'rgba(173,20,87,0.4)' },
    { fill: '#37474F', stroke: '#78909C', glow: 'rgba(55,71,79,0.3)' },
    { fill: '#827717', stroke: '#C0CA33', glow: 'rgba(130,119,23,0.4)' },
];

function buildDomainColorMap(tables: TableDef[]): Map<string, DomainColor> {
    const domains = [...new Set(tables.map((table) => table.name.split('_')[0]))].sort();
    return new Map(domains.map((domain, i) => [domain, PALETTE[i % PALETTE.length]]));
}

function getDomain(name: string, domainColorMap: Map<string, DomainColor>): DomainColor {
    const prefix = name.split('_')[0];
    return domainColorMap.get(prefix) ?? PALETTE[0];
}

interface GraphNode extends TableDef {
    refs: number;
    selfRefs: number;
    r: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
    domain: DomainColor;
    outgoing: { target: number; col: string }[];
    incoming: { source: number; col: string }[];
}

function buildGraph(
    tables: TableDef[],
    fks: FKDef[],
    domainColorMap: Map<string, DomainColor>,
): { nodes: GraphNode[]; edges: FKDef[] } {
    const refCount: Record<number, number> = {};
    tables.forEach((table) => {
        refCount[table.recid] = 0;
    });
    fks.forEach((fk) => {
        if (fk.to !== fk.from) {
            refCount[fk.to] = (refCount[fk.to] ?? 0) + 1;
        }
    });

    const outgoing: Record<number, { target: number; col: string }[]> = {};
    const incoming: Record<number, { source: number; col: string }[]> = {};
    tables.forEach((table) => {
        outgoing[table.recid] = [];
        incoming[table.recid] = [];
    });
    fks.forEach((fk) => {
        if (fk.from !== fk.to) {
            outgoing[fk.from].push({ target: fk.to, col: fk.col });
            incoming[fk.to].push({ source: fk.from, col: fk.col });
        }
    });

    const maxRef = Math.max(...Object.values(refCount), 1);
    const cx = 500;
    const cy = 400;
    const nodes: GraphNode[] = tables.map((table, index) => {
        const refs = refCount[table.recid] ?? 0;
        const r = 8 + (refs / maxRef) * 34;
        const angle = (index / tables.length) * Math.PI * 2;
        const spread = 220 + Math.random() * 120;

        return {
            ...table,
            refs,
            selfRefs: fks.filter((fk) => fk.from === table.recid && fk.to === table.recid).length,
            r,
            x: cx + Math.cos(angle) * spread,
            y: cy + Math.sin(angle) * spread,
            vx: 0,
            vy: 0,
            domain: getDomain(table.name, domainColorMap),
            outgoing: outgoing[table.recid],
            incoming: incoming[table.recid],
        };
    });

    return { nodes, edges: fks.filter((fk) => fk.from !== fk.to) };
}

function simulate(nodes: GraphNode[], edges: FKDef[], iterations = 250): void {
    const byRecid: Record<number, GraphNode> = {};
    nodes.forEach((node) => {
        byRecid[node.recid] = node;
    });

    const cx = 500;
    const cy = 400;

    for (let iter = 0; iter < iterations; iter += 1) {
        const alpha = 1 - iter / iterations;
        const repulsionStrength = 9000 * alpha;
        const attractionStrength = 0.004 * alpha;
        const centerStrength = 0.008 * alpha;

        for (let i = 0; i < nodes.length; i += 1) {
            for (let j = i + 1; j < nodes.length; j += 1) {
                const a = nodes[i];
                const b = nodes[j];
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                let dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const minDist = a.r + b.r + 10;
                if (dist < minDist) {
                    dist = minDist;
                }
                const force = repulsionStrength / (dist * dist);
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                a.vx -= fx;
                a.vy -= fy;
                b.vx += fx;
                b.vy += fy;
            }
        }

        edges.forEach((edge) => {
            const a = byRecid[edge.from];
            const b = byRecid[edge.to];
            if (!a || !b) {
                return;
            }
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const ideal = 90 + a.r + b.r;
            const force = (dist - ideal) * attractionStrength;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            a.vx += fx;
            a.vy += fy;
            b.vx -= fx;
            b.vy -= fy;
        });

        nodes.forEach((node) => {
            node.vx += (cx - node.x) * centerStrength;
            node.vy += (cy - node.y) * centerStrength;
            node.vx *= 0.82;
            node.vy *= 0.82;
            node.x += node.vx;
            node.y += node.vy;
        });
    }
}

const ServiceVisualizationPage = (): JSX.Element => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [hovered, setHovered] = useState<GraphNode | null>(null);
    const [dragging, setDragging] = useState<GraphNode | null>(null);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [loading, setLoading] = useState(true);
    const [tableCount, setTableCount] = useState(0);
    const [edgeCount, setEdgeCount] = useState(0);
    const [domainColorMap, setDomainColorMap] = useState<Map<string, DomainColor>>(new Map());
    const graphRef = useRef<{ nodes: GraphNode[]; edges: FKDef[] } | null>(null);
    const panStart = useRef<{ mx: number; my: number; panX: number; panY: number } | null>(null);
    const dragOffset = useRef({ x: 0, y: 0 });

    useEffect(() => {
        void (async () => {
            try {
                const schema = await fetchFullSchema() as any;

                const tables: TableDef[] = (schema.tables ?? []).map((table: any) => ({
                    recid: table.recid,
                    name: table.element_name,
                }));

                const fks: FKDef[] = (schema.foreign_keys ?? []).map((fk: any) => ({
                    from: fk.tables_recid,
                    to: fk.referenced_tables_recid,
                    col: fk.element_column_name,
                }));

                const colorMap = buildDomainColorMap(tables);
                setDomainColorMap(colorMap);
                const graph = buildGraph(tables, fks, colorMap);
                simulate(graph.nodes, graph.edges);
                graphRef.current = graph;
                setTableCount(tables.length);
                setEdgeCount(fks.filter((fk: FKDef) => fk.from !== fk.to).length);
            } catch (error) {
                console.error('Failed to load schema:', error);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const toWorld = useCallback(
        (sx: number, sy: number) => ({
            x: (sx - pan.x) / zoom,
            y: (sy - pan.y) / zoom,
        }),
        [pan, zoom],
    );

    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas || !graphRef.current) {
            return;
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            return;
        }

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, rect.width, rect.height);

        const { nodes, edges } = graphRef.current;
        const byRecid: Record<number, GraphNode> = {};
        nodes.forEach((node) => {
            byRecid[node.recid] = node;
        });

        ctx.save();
        ctx.translate(pan.x, pan.y);
        ctx.scale(zoom, zoom);

        edges.forEach((edge) => {
            const a = byRecid[edge.from];
            const b = byRecid[edge.to];
            if (!a || !b) {
                return;
            }

            const isHighlight = hovered != null && (hovered.recid === edge.from || hovered.recid === edge.to);

            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            if (isHighlight) {
                ctx.strokeStyle = '#4CAF50';
                ctx.lineWidth = 2;
                ctx.shadowColor = 'rgba(76,175,80,0.6)';
                ctx.shadowBlur = 8;
            } else {
                ctx.strokeStyle = 'rgba(255,255,255,0.08)';
                ctx.lineWidth = 0.7;
                ctx.shadowColor = 'transparent';
                ctx.shadowBlur = 0;
            }
            ctx.stroke();
            ctx.shadowBlur = 0;

            if (isHighlight) {
                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist > 0) {
                    const ux = dx / dist;
                    const uy = dy / dist;
                    const tipX = b.x - ux * b.r;
                    const tipY = b.y - uy * b.r;
                    const size = 7;
                    ctx.beginPath();
                    ctx.moveTo(tipX, tipY);
                    ctx.lineTo(tipX - ux * size - uy * size * 0.5, tipY - uy * size + ux * size * 0.5);
                    ctx.lineTo(tipX - ux * size + uy * size * 0.5, tipY - uy * size - ux * size * 0.5);
                    ctx.closePath();
                    ctx.fillStyle = '#4CAF50';
                    ctx.fill();
                }
            }
        });

        nodes.forEach((node) => {
            const isHovered = hovered != null && hovered.recid === node.recid;
            const isConnected =
                hovered != null &&
                (hovered.outgoing.some((outgoing) => outgoing.target === node.recid) ||
                    hovered.incoming.some((incoming) => incoming.source === node.recid) ||
                    node.outgoing.some((outgoing) => outgoing.target === hovered.recid) ||
                    node.incoming.some((incoming) => incoming.source === hovered.recid));
            const dimmed = hovered != null && !isHovered && !isConnected;

            if (isHovered) {
                ctx.shadowColor = node.domain.glow;
                ctx.shadowBlur = 24;
            } else if (isConnected) {
                ctx.shadowColor = node.domain.glow;
                ctx.shadowBlur = 12;
            } else {
                ctx.shadowColor = dimmed ? 'transparent' : node.domain.glow;
                ctx.shadowBlur = dimmed ? 0 : 6;
            }

            ctx.beginPath();
            ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
            ctx.fillStyle = dimmed ? `${node.domain.fill}22` : node.domain.fill;
            ctx.fill();
            ctx.strokeStyle = dimmed ? `${node.domain.stroke}33` : isHovered ? '#ffffff' : node.domain.stroke;
            ctx.lineWidth = isHovered ? 2.5 : 1.2;
            ctx.stroke();
            ctx.shadowBlur = 0;

            if (isHovered || (isConnected && zoom > 0.5)) {
                const fontSize = Math.max(10, 11 / zoom);
                ctx.font = `500 ${fontSize}px "Roboto", "Arial", sans-serif`;
                ctx.textAlign = 'center';

                ctx.fillStyle = '#000000';
                ctx.fillText(node.name, node.x + 1, node.y - node.r - 6 + 1);
                ctx.fillStyle = isHovered ? '#ffffff' : node.domain.stroke;
                ctx.fillText(node.name, node.x, node.y - node.r - 6);
            }
        });

        ctx.restore();
    }, [hovered, pan, zoom]);

    useEffect(() => {
        draw();
    }, [draw]);

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

    const findNode = useCallback(
        (sx: number, sy: number): GraphNode | null => {
            if (!graphRef.current) {
                return null;
            }
            const world = toWorld(sx, sy);
            let closest: GraphNode | null = null;
            let closestDist = Infinity;
            graphRef.current.nodes.forEach((node) => {
                const dx = node.x - world.x;
                const dy = node.y - world.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < node.r + 5 && dist < closestDist) {
                    closest = node;
                    closestDist = dist;
                }
            });
            return closest;
        },
        [toWorld],
    );

    const handleMouseMove = useCallback(
        (event: MouseEvent<HTMLCanvasElement>) => {
            const canvas = canvasRef.current;
            if (!canvas) {
                return;
            }

            const rect = canvas.getBoundingClientRect();
            const sx = event.clientX - rect.left;
            const sy = event.clientY - rect.top;

            if (dragging) {
                const world = toWorld(sx, sy);
                dragging.x = world.x - dragOffset.current.x;
                dragging.y = world.y - dragOffset.current.y;
                draw();
                return;
            }

            if (panStart.current) {
                setPan({
                    x: panStart.current.panX + (event.clientX - panStart.current.mx),
                    y: panStart.current.panY + (event.clientY - panStart.current.my),
                });
                return;
            }

            const node = findNode(sx, sy);
            setHovered(node);
            canvas.style.cursor = node ? 'pointer' : 'grab';
        },
        [dragging, draw, findNode, toWorld],
    );

    const handleMouseDown = useCallback(
        (event: MouseEvent<HTMLCanvasElement>) => {
            const canvas = canvasRef.current;
            if (!canvas) {
                return;
            }

            const rect = canvas.getBoundingClientRect();
            const sx = event.clientX - rect.left;
            const sy = event.clientY - rect.top;
            const node = findNode(sx, sy);

            if (node) {
                const world = toWorld(sx, sy);
                dragOffset.current = { x: world.x - node.x, y: world.y - node.y };
                setDragging(node);
            } else {
                panStart.current = {
                    mx: event.clientX,
                    my: event.clientY,
                    panX: pan.x,
                    panY: pan.y,
                };
            }
        },
        [findNode, pan.x, pan.y, toWorld],
    );

    const handleMouseUp = useCallback(() => {
        setDragging(null);
        panStart.current = null;
    }, []);

    const handleWheel = useCallback(
        (event: WheelEvent) => {
            event.preventDefault();
            const canvas = canvasRef.current;
            if (!canvas) {
                return;
            }

            const rect = canvas.getBoundingClientRect();
            const sx = event.clientX - rect.left;
            const sy = event.clientY - rect.top;
            const factor = event.deltaY < 0 ? 1.1 : 0.9;
            const newZoom = Math.max(0.15, Math.min(5, zoom * factor));
            setPan({
                x: sx - (sx - pan.x) * (newZoom / zoom),
                y: sy - (sy - pan.y) * (newZoom / zoom),
            });
            setZoom(newZoom);
        },
        [pan.x, pan.y, zoom],
    );

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) {
            return;
        }
        canvas.addEventListener('wheel', handleWheel, { passive: false });
        return () => {
            canvas.removeEventListener('wheel', handleWheel);
        };
    }, [handleWheel]);

    const byRecid: Record<number, GraphNode> = {};
    if (graphRef.current) {
        graphRef.current.nodes.forEach((node) => {
            byRecid[node.recid] = node;
        });
    }
    const legend = Array.from(domainColorMap.entries()).map(([domain, color]) => ({
        label: domain.charAt(0).toUpperCase() + domain.slice(1),
        color,
    }));

    if (loading) {
        return (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '50vh' }}>
                <Typography sx={{ color: '#555', fontSize: '0.85rem' }}>Loading schema data...</Typography>
            </Box>
        );
    }

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                height: 'calc(100vh - 28px)',
                mx: '-18px',
                mt: '-14px',
            }}
        >
            <Box
                sx={{
                    px: '18px',
                    pt: '14px',
                    pb: '8px',
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: 2,
                    flexWrap: 'wrap',
                    borderBottom: '1px solid #1A1A1A',
                }}
            >
                <PageTitle>Schema Visualization</PageTitle>
                <Typography variant="body2" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    {tableCount} tables &middot; {edgeCount} relationships
                </Typography>
                <Box sx={{ ml: 'auto', display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                    {legend.map((item) => (
                        <Box
                            key={item.label}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                fontSize: '0.65rem',
                                color: '#888',
                            }}
                        >
                            <Box
                                sx={{
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    bgcolor: item.color.fill,
                                    border: `1px solid ${item.color.stroke}`,
                                    boxShadow: `0 0 4px ${item.color.glow}`,
                                }}
                            />
                            {item.label}
                        </Box>
                    ))}
                </Box>
            </Box>

            <canvas
                ref={canvasRef}
                style={{
                    flex: 1,
                    cursor: 'grab',
                    minHeight: 0,
                    background: '#000000',
                }}
                onMouseMove={handleMouseMove}
                onMouseDown={handleMouseDown}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            />

            <Box
                sx={{
                    minHeight: '44px',
                    maxHeight: hovered ? '220px' : '44px',
                    overflow: 'auto',
                    borderTop: '1px solid #1A1A1A',
                    bgcolor: '#000',
                    px: '18px',
                    py: '10px',
                    transition: 'max-height 0.15s ease',
                }}
            >
                {!hovered ? (
                    <Typography variant="body2" sx={{ color: '#444', fontSize: '0.75rem', fontStyle: 'italic' }}>
                        Hover over a node to inspect. Scroll to zoom, drag to pan, drag nodes to reposition.
                    </Typography>
                ) : (
                    <Box
                        sx={{
                            display: 'grid',
                            gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr) minmax(0,1fr)',
                            gap: 2,
                        }}
                    >
                        <Box>
                            <Typography
                                sx={{
                                    fontSize: '0.6rem',
                                    color: '#555',
                                    textTransform: 'uppercase',
                                    letterSpacing: 1,
                                    mb: '2px',
                                }}
                            >
                                Table
                            </Typography>
                            <Typography
                                sx={{
                                    fontSize: '0.95rem',
                                    fontWeight: 600,
                                    color: hovered.domain.stroke,
                                    fontFamily: '"Roboto Mono", monospace',
                                    textShadow: `0 0 8px ${hovered.domain.glow}`,
                                }}
                            >
                                {hovered.name}
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#888', fontSize: '0.7rem', mt: '4px' }}>
                                Domain: <span style={{ fontWeight: 600 }}>{hovered.name.split('_')[0]}</span>
                                {hovered.selfRefs > 0 && (
                                    <>
                                        {' · '}
                                        <span style={{ fontWeight: 600 }}>
                                            {hovered.selfRefs} self-ref{hovered.selfRefs > 1 ? 's' : ''}
                                        </span>
                                    </>
                                )}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1.5, mt: 1 }}>
                                <Box
                                    sx={{
                                        bgcolor: '#0A0A0A',
                                        border: '1px solid #1A1A1A',
                                        borderRadius: '4px',
                                        px: 1.5,
                                        py: 0.5,
                                        textAlign: 'center',
                                    }}
                                >
                                    <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: '#4CAF50' }}>
                                        {hovered.refs}
                                    </Typography>
                                    <Typography
                                        sx={{
                                            fontSize: '0.55rem',
                                            color: '#555',
                                            textTransform: 'uppercase',
                                        }}
                                    >
                                        Referenced by
                                    </Typography>
                                </Box>
                                <Box
                                    sx={{
                                        bgcolor: '#0A0A0A',
                                        border: '1px solid #1A1A1A',
                                        borderRadius: '4px',
                                        px: 1.5,
                                        py: 0.5,
                                        textAlign: 'center',
                                    }}
                                >
                                    <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: '#BF8C2C' }}>
                                        {hovered.outgoing.length}
                                    </Typography>
                                    <Typography
                                        sx={{
                                            fontSize: '0.55rem',
                                            color: '#555',
                                            textTransform: 'uppercase',
                                        }}
                                    >
                                        References
                                    </Typography>
                                </Box>
                            </Box>
                        </Box>

                        <Box>
                            <Typography
                                sx={{
                                    fontSize: '0.6rem',
                                    color: '#555',
                                    textTransform: 'uppercase',
                                    letterSpacing: 1,
                                    mb: '4px',
                                }}
                            >
                                Outgoing FK
                            </Typography>
                            {hovered.outgoing.length === 0 ? (
                                <Typography sx={{ fontSize: '0.7rem', color: '#333', fontStyle: 'italic' }}>
                                    None (root table)
                                </Typography>
                            ) : (
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                                    {hovered.outgoing.map((outgoing) => (
                                        <Typography key={`${outgoing.col}-${outgoing.target}`} sx={{ fontSize: '0.7rem', color: '#ccc' }}>
                                            <span
                                                style={{
                                                    fontFamily: '"Roboto Mono", monospace',
                                                    color: '#666',
                                                    fontSize: '0.65rem',
                                                }}
                                            >
                                                {outgoing.col}
                                            </span>
                                            {' → '}
                                            <span
                                                style={{
                                                    fontWeight: 600,
                                                    color: byRecid[outgoing.target]?.domain.stroke ?? '#888',
                                                }}
                                            >
                                                {byRecid[outgoing.target]?.name ?? `recid:${outgoing.target}`}
                                            </span>
                                        </Typography>
                                    ))}
                                </Box>
                            )}
                        </Box>

                        <Box>
                            <Typography
                                sx={{
                                    fontSize: '0.6rem',
                                    color: '#555',
                                    textTransform: 'uppercase',
                                    letterSpacing: 1,
                                    mb: '4px',
                                }}
                            >
                                Incoming FK
                            </Typography>
                            {hovered.incoming.length === 0 ? (
                                <Typography sx={{ fontSize: '0.7rem', color: '#333', fontStyle: 'italic' }}>
                                    None (leaf table)
                                </Typography>
                            ) : (
                                <Box
                                    sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '1px',
                                        maxHeight: '120px',
                                        overflow: 'auto',
                                    }}
                                >
                                    {hovered.incoming.map((incoming) => (
                                        <Typography key={`${incoming.col}-${incoming.source}`} sx={{ fontSize: '0.7rem', color: '#ccc' }}>
                                            <span
                                                style={{
                                                    fontWeight: 600,
                                                    color: byRecid[incoming.source]?.domain.stroke ?? '#888',
                                                }}
                                            >
                                                {byRecid[incoming.source]?.name ?? `recid:${incoming.source}`}
                                            </span>
                                            {' via '}
                                            <span
                                                style={{
                                                    fontFamily: '"Roboto Mono", monospace',
                                                    color: '#666',
                                                    fontSize: '0.65rem',
                                                }}
                                            >
                                                {incoming.col}
                                            </span>
                                        </Typography>
                                    ))}
                                </Box>
                            )}
                        </Box>
                    </Box>
                )}
            </Box>
        </Box>
    );
};

export default ServiceVisualizationPage;
