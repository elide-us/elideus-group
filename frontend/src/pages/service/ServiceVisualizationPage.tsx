import { useEffect, useRef, useState, useCallback, type MouseEvent } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import PageTitle from '../../components/PageTitle';

interface TableDef {
    recid: number;
    name: string;
}

interface FKDef {
    from: number;
    to: number;
    col: string;
}

const TABLES: TableDef[] = [
    { recid: 1, name: 'auth_providers' },
    { recid: 2, name: 'account_users' },
    { recid: 3, name: 'users_sessions' },
    { recid: 4, name: 'storage_types' },
    { recid: 5, name: 'users_auth' },
    { recid: 6, name: 'account_actions' },
    { recid: 7, name: 'users_storage_cache' },
    { recid: 8, name: 'frontend_links' },
    { recid: 9, name: 'frontend_routes' },
    { recid: 10, name: 'system_config' },
    { recid: 11, name: 'users_credits' },
    { recid: 12, name: 'users_enablements' },
    { recid: 13, name: 'users_profileimg' },
    { recid: 14, name: 'users_roles' },
    { recid: 15, name: 'system_roles' },
    { recid: 16, name: 'discord_guilds' },
    { recid: 17, name: 'sessions_devices' },
    { recid: 18, name: 'users_actions_log' },
    { recid: 19, name: 'assistant_models' },
    { recid: 20, name: 'assistant_personas' },
    { recid: 21, name: 'assistant_conversations' },
    { recid: 22, name: 'service_pages' },
    { recid: 23, name: 'system_edt_mappings' },
    { recid: 24, name: 'system_schema_tables' },
    { recid: 25, name: 'system_schema_columns' },
    { recid: 26, name: 'system_schema_indexes' },
    { recid: 27, name: 'system_schema_foreign_keys' },
    { recid: 28, name: 'builder_categories' },
    { recid: 29, name: 'finance_accounts' },
    { recid: 30, name: 'finance_numbers' },
    { recid: 31, name: 'finance_periods' },
    { recid: 32, name: 'system_schema_views' },
    { recid: 33, name: 'discord_channels' },
    { recid: 34, name: 'finance_dimensions' },
    { recid: 35, name: 'finance_journals' },
    { recid: 36, name: 'finance_ledgers' },
    { recid: 37, name: 'account_api_tokens' },
    { recid: 38, name: 'account_mcp_agents' },
    { recid: 39, name: 'account_mcp_agent_tokens' },
    { recid: 40, name: 'account_mcp_auth_codes' },
    { recid: 41, name: 'system_batch_jobs' },
    { recid: 42, name: 'system_batch_job_history' },
    { recid: 43, name: 'finance_journal_lines' },
    { recid: 44, name: 'finance_journal_line_dimensions' },
    { recid: 45, name: 'finance_credit_lots' },
    { recid: 46, name: 'finance_credit_lot_events' },
    { recid: 47, name: 'finance_staging_imports' },
    { recid: 48, name: 'finance_staging_azure_cost_details' },
    { recid: 49, name: 'system_async_tasks' },
    { recid: 50, name: 'system_async_task_events' },
    { recid: 51, name: 'finance_staging_account_map' },
    { recid: 52, name: 'finance_vendors' },
    { recid: 53, name: 'finance_staging_line_items' },
    { recid: 54, name: 'finance_staging_azure_invoices' },
    { recid: 55, name: 'finance_staging_purge_log' },
    { recid: 56, name: 'system_renewals' },
    { recid: 57, name: 'finance_status_codes' },
    { recid: 58, name: 'finance_pipeline_config' },
    { recid: 59, name: 'finance_products' },
    { recid: 60, name: 'finance_product_journal_config' },
];

const FKS: FKDef[] = [
    { from: 2, to: 1, col: 'providers_recid' },
    { from: 3, to: 2, col: 'users_guid' },
    { from: 5, to: 1, col: 'providers_recid' },
    { from: 5, to: 2, col: 'users_guid' },
    { from: 7, to: 6, col: 'moderation_recid' },
    { from: 7, to: 2, col: 'users_guid' },
    { from: 7, to: 4, col: 'types_recid' },
    { from: 11, to: 2, col: 'users_guid' },
    { from: 12, to: 2, col: 'users_guid' },
    { from: 13, to: 1, col: 'providers_recid' },
    { from: 13, to: 2, col: 'users_guid' },
    { from: 14, to: 2, col: 'users_guid' },
    { from: 17, to: 1, col: 'providers_recid' },
    { from: 17, to: 3, col: 'sessions_guid' },
    { from: 18, to: 6, col: 'action_recid' },
    { from: 18, to: 2, col: 'users_guid' },
    { from: 20, to: 19, col: 'models_recid' },
    { from: 21, to: 19, col: 'models_recid' },
    { from: 21, to: 20, col: 'personas_recid' },
    { from: 21, to: 2, col: 'users_guid' },
    { from: 22, to: 2, col: 'element_created_by' },
    { from: 22, to: 2, col: 'element_modified_by' },
    { from: 25, to: 23, col: 'edt_recid' },
    { from: 25, to: 24, col: 'tables_recid' },
    { from: 26, to: 24, col: 'tables_recid' },
    { from: 27, to: 24, col: 'referenced_tables_recid' },
    { from: 27, to: 24, col: 'tables_recid' },
    { from: 29, to: 29, col: 'element_parent' },
    { from: 30, to: 29, col: 'accounts_guid' },
    { from: 33, to: 16, col: 'guilds_recid' },
    { from: 35, to: 30, col: 'numbers_recid' },
    { from: 35, to: 31, col: 'periods_guid' },
    { from: 35, to: 36, col: 'ledgers_recid' },
    { from: 35, to: 35, col: 'element_reversed_by' },
    { from: 35, to: 35, col: 'element_reversal_of' },
    { from: 36, to: 29, col: 'element_chart_of_accounts_guid' },
    { from: 37, to: 2, col: 'users_recid' },
    { from: 38, to: 2, col: 'users_recid' },
    { from: 39, to: 38, col: 'agents_recid' },
    { from: 40, to: 38, col: 'agents_recid' },
    { from: 40, to: 2, col: 'users_recid' },
    { from: 42, to: 41, col: 'jobs_recid' },
    { from: 43, to: 35, col: 'journals_recid' },
    { from: 43, to: 29, col: 'accounts_guid' },
    { from: 44, to: 43, col: 'lines_recid' },
    { from: 44, to: 34, col: 'dimensions_recid' },
    { from: 45, to: 2, col: 'users_guid' },
    { from: 45, to: 30, col: 'numbers_recid' },
    { from: 46, to: 45, col: 'lots_recid' },
    { from: 46, to: 35, col: 'journals_recid' },
    { from: 50, to: 49, col: 'tasks_recid' },
    { from: 53, to: 47, col: 'imports_recid' },
    { from: 53, to: 52, col: 'vendors_recid' },
    { from: 51, to: 29, col: 'accounts_guid' },
    { from: 51, to: 52, col: 'vendors_recid' },
    { from: 54, to: 47, col: 'imports_recid' },
    { from: 55, to: 52, col: 'vendors_recid' },
    { from: 48, to: 47, col: 'imports_recid' },
    { from: 31, to: 30, col: 'numbers_recid' },
    { from: 60, to: 35, col: 'journals_recid' },
    { from: 60, to: 31, col: 'periods_guid' },
];

interface DomainColor {
    fill: string;
    stroke: string;
    glow: string;
}

const DOMAIN_COLORS: Record<string, DomainColor> = {
    account: { fill: '#4CAF50', stroke: '#81C784', glow: 'rgba(76,175,80,0.5)' },
    users: { fill: '#388E3C', stroke: '#66BB6A', glow: 'rgba(56,142,60,0.4)' },
    sessions: { fill: '#2E7D32', stroke: '#4CAF50', glow: 'rgba(46,125,50,0.35)' },
    auth: { fill: '#1B5E20', stroke: '#43A047', glow: 'rgba(27,94,32,0.35)' },
    finance: { fill: '#BF8C2C', stroke: '#D4A845', glow: 'rgba(191,140,44,0.5)' },
    system: { fill: '#1565C0', stroke: '#42A5F5', glow: 'rgba(21,101,192,0.4)' },
    assistant: { fill: '#00838F', stroke: '#26C6DA', glow: 'rgba(0,131,143,0.4)' },
    discord: { fill: '#5865F2', stroke: '#7983F5', glow: 'rgba(88,101,242,0.4)' },
    frontend: { fill: '#6A1B9A', stroke: '#AB47BC', glow: 'rgba(106,27,154,0.4)' },
    service: { fill: '#6A1B9A', stroke: '#AB47BC', glow: 'rgba(106,27,154,0.4)' },
    storage: { fill: '#546E7A', stroke: '#90A4AE', glow: 'rgba(84,110,122,0.3)' },
    builder: { fill: '#546E7A', stroke: '#90A4AE', glow: 'rgba(84,110,122,0.3)' },
};

function getDomain(name: string): DomainColor {
    const prefix = name.split('_')[0];
    return DOMAIN_COLORS[prefix] ?? DOMAIN_COLORS.system;
}

interface GraphNode extends TableDef {
    refs: number;
    r: number;
    x: number;
    y: number;
    vx: number;
    vy: number;
    domain: DomainColor;
    outgoing: { target: number; col: string }[];
    incoming: { source: number; col: string }[];
}

function buildGraph(): { nodes: GraphNode[]; edges: FKDef[] } {
    const refCount: Record<number, number> = {};
    TABLES.forEach((table) => {
        refCount[table.recid] = 0;
    });
    FKS.forEach((fk) => {
        if (fk.to !== fk.from) {
            refCount[fk.to] = (refCount[fk.to] ?? 0) + 1;
        }
    });

    const outgoing: Record<number, { target: number; col: string }[]> = {};
    const incoming: Record<number, { source: number; col: string }[]> = {};
    TABLES.forEach((table) => {
        outgoing[table.recid] = [];
        incoming[table.recid] = [];
    });
    FKS.forEach((fk) => {
        if (fk.from !== fk.to) {
            outgoing[fk.from].push({ target: fk.to, col: fk.col });
            incoming[fk.to].push({ source: fk.from, col: fk.col });
        }
    });

    const maxRef = Math.max(...Object.values(refCount), 1);
    const cx = 500;
    const cy = 400;
    const nodes: GraphNode[] = TABLES.map((table, index) => {
        const refs = refCount[table.recid] ?? 0;
        const r = 8 + (refs / maxRef) * 34;
        const angle = (index / TABLES.length) * Math.PI * 2;
        const spread = 220 + Math.random() * 120;

        return {
            ...table,
            refs,
            r,
            x: cx + Math.cos(angle) * spread,
            y: cy + Math.sin(angle) * spread,
            vx: 0,
            vy: 0,
            domain: getDomain(table.name),
            outgoing: outgoing[table.recid],
            incoming: incoming[table.recid],
        };
    });

    return { nodes, edges: FKS.filter((fk) => fk.from !== fk.to) };
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

const LEGEND = [
    { label: 'Account / Identity', color: DOMAIN_COLORS.account },
    { label: 'Finance', color: DOMAIN_COLORS.finance },
    { label: 'System', color: DOMAIN_COLORS.system },
    { label: 'Assistant', color: DOMAIN_COLORS.assistant },
    { label: 'Discord', color: DOMAIN_COLORS.discord },
    { label: 'Frontend / Service', color: DOMAIN_COLORS.frontend },
    { label: 'Storage / Builder', color: DOMAIN_COLORS.storage },
];

const ServiceVisualizationPage = (): JSX.Element => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [hovered, setHovered] = useState<GraphNode | null>(null);
    const [dragging, setDragging] = useState<GraphNode | null>(null);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const graphRef = useRef<{ nodes: GraphNode[]; edges: FKDef[] } | null>(null);
    const panStart = useRef<{ mx: number; my: number; panX: number; panY: number } | null>(null);
    const dragOffset = useRef({ x: 0, y: 0 });

    useEffect(() => {
        const graph = buildGraph();
        simulate(graph.nodes, graph.edges);
        graphRef.current = graph;
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

    const selfRefs = hovered ? FKS.filter((fk) => fk.from === hovered.recid && fk.to === hovered.recid) : [];

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
                    {TABLES.length} tables &middot; {FKS.filter((fk) => fk.from !== fk.to).length} relationships
                </Typography>
                <Box sx={{ ml: 'auto', display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                    {LEGEND.map((item) => (
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
                                {selfRefs.length > 0 && (
                                    <>
                                        {' · '}
                                        <span style={{ fontWeight: 600 }}>
                                            {selfRefs.length} self-ref{selfRefs.length > 1 ? 's' : ''}
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
