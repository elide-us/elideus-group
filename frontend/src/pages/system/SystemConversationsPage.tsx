import { useEffect, useState } from "react";
import {
    Box,
    Button,
    Divider,
    MenuItem,
    Paper,
    Stack,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Tabs,
    TextField,
    Typography,
} from "@mui/material";

import PageTitle from "../../components/PageTitle";
import {
    fetchDeleteBefore,
    fetchDeleteThread,
    fetchStats,
    fetchListConversations,
    fetchViewThread,
} from "../../rpc/system/conversations";
import type {
    SystemConversationsConversationItem1,
    SystemConversationsStats1,
    SystemConversationsThread1,
} from "../../shared/RpcModels";

interface TabPanelProps {
    children?: React.ReactNode;
    value: number;
    index: number;
}

function TabPanel({ children, value, index }: TabPanelProps): JSX.Element {
    if (value !== index) {
        return <></>;
    }
    return <Box sx={{ pt: 2 }}>{children}</Box>;
}

const truncateThreadId = (threadId?: string | null): string => {
    if (!threadId) return "";
    if (threadId.length <= 18) return threadId;
    return `${threadId.slice(0, 8)}...${threadId.slice(-6)}`;
};

const SystemConversationsPage = (): JSX.Element => {
    const [tab, setTab] = useState(0);
    const [forbidden, setForbidden] = useState(false);
    const [stats, setStats] = useState<SystemConversationsStats1 | null>(null);
    const [statsDeleted, setStatsDeleted] = useState<number | null>(null);
    const [before, setBefore] = useState("");

    const [limit, setLimit] = useState(50);
    const [offset, setOffset] = useState(0);
    const [rows, setRows] = useState<SystemConversationsConversationItem1[]>([]);

    const [threadId, setThreadId] = useState("");
    const [thread, setThread] = useState<SystemConversationsThread1 | null>(null);

    const loadStats = async (): Promise<void> => {
        try {
            const res: SystemConversationsStats1 = await fetchStats({});
            setStats(res);
            setForbidden(false);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            }
        }
    };

    const loadBrowse = async (nextOffset: number = offset, nextLimit: number = limit): Promise<void> => {
        try {
            const res = await fetchListConversations({ limit: nextLimit, offset: nextOffset });
            setRows(res.conversations || []);
            setForbidden(false);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            }
        }
    };

    const loadThread = async (target: string = threadId): Promise<void> => {
        if (!target.trim()) return;
        try {
            const res: SystemConversationsThread1 = await fetchViewThread({ thread_id: target.trim() });
            setThread(res);
            setForbidden(false);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            }
        }
    };

    useEffect(() => {
        void loadStats();
        void loadBrowse(0, limit);
    }, []);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>System Conversations</PageTitle>
            <Tabs value={tab} onChange={(_e, v) => setTab(v)} aria-label="system conversations tabs">
                <Tab label="Overview" />
                <Tab label="Browse" />
                <Tab label="Thread Viewer" />
            </Tabs>
            <Divider sx={{ my: 2 }} />

            <TabPanel value={tab} index={0}>
                <Stack spacing={2} sx={{ maxWidth: 800 }}>
                    <Stack direction="row" spacing={2}>
                        <Button variant="outlined" onClick={() => { void loadStats(); }}>Refresh</Button>
                    </Stack>
                    <Paper sx={{ p: 2 }}>
                        <Typography>Total Rows: {stats?.total_rows ?? 0}</Typography>
                        <Typography>Total Threads: {stats?.total_threads ?? 0}</Typography>
                        <Typography>Oldest Entry: {stats?.oldest_entry ?? "-"}</Typography>
                        <Typography>Newest Entry: {stats?.newest_entry ?? "-"}</Typography>
                        <Typography>Total Tokens: {stats?.total_tokens ?? 0}</Typography>
                    </Paper>
                    <Stack direction="row" spacing={2} alignItems="center">
                        <TextField
                            label="Delete before (ISO datetime)"
                            value={before}
                            onChange={(e) => setBefore(e.target.value)}
                            placeholder="2025-01-01T00:00:00Z"
                            sx={{ minWidth: 320 }}
                        />
                        <Button
                            color="error"
                            variant="contained"
                            onClick={async () => {
                                if (!before.trim()) return;
                                if (!window.confirm(`Delete all conversations before ${before}?`)) return;
                                const res = await fetchDeleteBefore({ before: before.trim() });
                                setStatsDeleted(res.deleted ?? 0);
                                await loadStats();
                                await loadBrowse(0, limit);
                            }}
                        >
                            Delete
                        </Button>
                    </Stack>
                    {statsDeleted !== null && <Typography>Deleted {statsDeleted} rows</Typography>}
                </Stack>
            </TabPanel>

            <TabPanel value={tab} index={1}>
                <Stack spacing={2}>
                    <Stack direction="row" spacing={2} alignItems="center">
                        <TextField
                            select
                            label="Limit"
                            value={limit}
                            onChange={async (e) => {
                                const nextLimit = Number(e.target.value);
                                setLimit(nextLimit);
                                setOffset(0);
                                await loadBrowse(0, nextLimit);
                            }}
                            sx={{ width: 120 }}
                        >
                            {[25, 50, 100].map((val) => (
                                <MenuItem key={val} value={val}>{val}</MenuItem>
                            ))}
                        </TextField>
                        <Button
                            variant="outlined"
                            disabled={offset === 0}
                            onClick={async () => {
                                const nextOffset = Math.max(0, offset - limit);
                                setOffset(nextOffset);
                                await loadBrowse(nextOffset, limit);
                            }}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outlined"
                            disabled={rows.length < limit}
                            onClick={async () => {
                                const nextOffset = offset + limit;
                                setOffset(nextOffset);
                                await loadBrowse(nextOffset, limit);
                            }}
                        >
                            Next
                        </Button>
                        <Typography>Offset: {offset}</Typography>
                    </Stack>

                    <Table size="small" sx={{ "& td, & th": { py: 0.75, verticalAlign: "top" } }}>
                        <TableHead>
                            <TableRow>
                                <TableCell>Timestamp</TableCell>
                                <TableCell>Persona</TableCell>
                                <TableCell>Role</TableCell>
                                <TableCell>Thread ID</TableCell>
                                <TableCell>Preview</TableCell>
                                <TableCell>Tokens</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {rows.map((row) => (
                                <TableRow key={row.recid}>
                                    <TableCell>{row.created_on || "-"}</TableCell>
                                    <TableCell>{row.persona_name || row.personas_recid}</TableCell>
                                    <TableCell>{row.role || "-"}</TableCell>
                                    <TableCell>
                                        {row.thread_id ? (
                                            <Button
                                                size="small"
                                                onClick={async () => {
                                                    const nextThreadId = row.thread_id || "";
                                                    setThreadId(nextThreadId);
                                                    setTab(2);
                                                    await loadThread(nextThreadId);
                                                }}
                                            >
                                                {truncateThreadId(row.thread_id)}
                                            </Button>
                                        ) : "-"}
                                    </TableCell>
                                    <TableCell>{row.preview || ""}</TableCell>
                                    <TableCell>{row.tokens ?? "-"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            </TabPanel>

            <TabPanel value={tab} index={2}>
                <Stack spacing={2}>
                    <Stack direction="row" spacing={2}>
                        <TextField
                            label="Thread ID"
                            value={threadId}
                            onChange={(e) => setThreadId(e.target.value)}
                            sx={{ minWidth: 420 }}
                        />
                        <Button variant="outlined" onClick={() => { void loadThread(); }}>Load</Button>
                    </Stack>

                    <Stack spacing={1}>
                        {(thread?.messages || []).map((message) => (
                            <Paper key={message.recid} sx={{ p: 1.5 }}>
                                <Typography variant="caption">
                                    {(message.role || "unknown").toUpperCase()} — {message.created_on || "-"}
                                </Typography>
                                <Typography sx={{ whiteSpace: "pre-wrap" }}>{message.content || ""}</Typography>
                            </Paper>
                        ))}
                    </Stack>

                    <Box>
                        <Button
                            color="error"
                            variant="contained"
                            disabled={!threadId.trim()}
                            onClick={async () => {
                                if (!threadId.trim()) return;
                                if (!window.confirm(`Delete thread ${threadId}?`)) return;
                                await fetchDeleteThread({ thread_id: threadId.trim() });
                                setThread(null);
                                await loadStats();
                                await loadBrowse(offset, limit);
                            }}
                        >
                            Delete Thread
                        </Button>
                    </Box>
                </Stack>
            </TabPanel>
        </Box>
    );
};

export default SystemConversationsPage;
