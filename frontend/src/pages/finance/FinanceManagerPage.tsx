import { useCallback, useEffect, useMemo, useState } from "react";
import {
    Box,
    Button,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
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
import { rpcCall } from "../../shared/RpcModels";

type StagingImport = {
    recid: number;
    element_source: string;
    element_scope: string | null;
    element_metric: string;
    element_period_start: string;
    element_period_end: string;
    element_row_count: number;
    element_status: number;
    element_error: string | null;
    element_created_on: string;
    element_modified_on: string;
    element_requested_by: string | null;
    element_approved_by: string | null;
    element_approved_on: string | null;
};

type StagingLineItem = {
    recid: number;
    imports_recid: number;
    vendor_name: string | null;
    element_date: string | null;
    element_service: string | null;
    element_category: string | null;
    element_description: string | null;
    element_quantity: string | null;
    element_amount: string;
    element_currency: string | null;
};

type PeriodStatus = {
    period_guid: string;
    fiscal_year: number;
    period_number: number;
    period_name: string;
    start_date: string;
    end_date: string;
    close_type: number;
    period_status: number;
    has_closing_week: boolean;
    total_journals: number;
    draft_journals: number;
    pending_journals: number;
    posted_journals: number;
    reversed_journals: number;
};

type TrialBalanceRow = {
    period_guid: string;
    fiscal_year: number;
    period_number: number;
    period_name: string;
    account_guid: string;
    account_number: string;
    account_name: string;
    account_type: number;
    total_debit: number;
    total_credit: number;
    net_balance: number;
};

type JournalSummaryRow = {
    recid: number;
    journal_name: string;
    journal_description: string | null;
    posting_key: string | null;
    source_type: string | null;
    source_id: string | null;
    journal_status: number;
    periods_guid: string | null;
    fiscal_year: number | null;
    period_name: string | null;
    posted_by: string | null;
    posted_on: string | null;
    reversed_by: number | null;
    reversal_of: number | null;
    created_on: string;
    line_count: number;
    total_debit: number;
    total_credit: number;
};

type JournalLine = {
    recid: number;
    journals_recid: number;
    line_number: number;
    accounts_guid: string;
    debit: string;
    credit: string;
    description: string | null;
    dimension_recids: number[];
};

const IMPORT_STATUS_CONFIG: Record<number, { label: string; color: "default" | "success" | "error" | "info" | "warning" }> = {
    0: { label: "Pending", color: "warning" },
    1: { label: "Approved", color: "success" },
    2: { label: "Failed", color: "error" },
    3: { label: "Promoted", color: "info" },
    4: { label: "Pending Approval", color: "warning" },
    5: { label: "Rejected", color: "error" },
};

const JOURNAL_STATUS_CONFIG: Record<number, { label: string; color: "warning" | "info" | "success" | "error" }> = {
    0: { label: "Draft", color: "warning" },
    1: { label: "Pending", color: "info" },
    2: { label: "Posted", color: "success" },
    3: { label: "Reversed", color: "error" },
};

const PERIOD_STATUS_CONFIG: Record<number, { label: string; color: "success" | "error" }> = {
    1: { label: "Open", color: "success" },
    2: { label: "Closed", color: "error" },
    3: { label: "Locked", color: "error" },
};

const getPeriodChipColor = (row: PeriodStatus): "warning" | "success" | "error" => {
    if (row.draft_journals > 0 || row.pending_journals > 0) {
        return "warning";
    }
    return PERIOD_STATUS_CONFIG[row.period_status]?.color || "error";
};

const FinanceManagerPage = (): JSX.Element => {
    const [tab, setTab] = useState(0);
    const [forbidden, setForbidden] = useState(false);

    const [approvalQueue, setApprovalQueue] = useState<StagingImport[]>([]);
    const [selectedImport, setSelectedImport] = useState<number | null>(null);
    const [approvalLineItems, setApprovalLineItems] = useState<StagingLineItem[]>([]);
    const [rejectImportDialogOpen, setRejectImportDialogOpen] = useState(false);
    const [rejectImportReason, setRejectImportReason] = useState("");

    const [allPeriodStatusRows, setAllPeriodStatusRows] = useState<PeriodStatus[]>([]);
    const [periodYear, setPeriodYear] = useState<number>(new Date().getFullYear());
    const [periodStatusRows, setPeriodStatusRows] = useState<PeriodStatus[]>([]);

    const [trialYear, setTrialYear] = useState<number>(new Date().getFullYear());
    const [trialPeriodGuid, setTrialPeriodGuid] = useState("");
    const [trialRows, setTrialRows] = useState<TrialBalanceRow[]>([]);

    const [journalYear, setJournalYear] = useState<number>(new Date().getFullYear());
    const [journalPeriodGuid, setJournalPeriodGuid] = useState("");
    const [journalStatus, setJournalStatus] = useState<string>("");
    const [journalRows, setJournalRows] = useState<JournalSummaryRow[]>([]);

    const [pendingJournals, setPendingJournals] = useState<JournalSummaryRow[]>([]);
    const [selectedPendingJournal, setSelectedPendingJournal] = useState<number | null>(null);
    const [pendingJournalLines, setPendingJournalLines] = useState<JournalLine[]>([]);
    const [rejectJournalDialogOpen, setRejectJournalDialogOpen] = useState(false);
    const [rejectJournalReason, setRejectJournalReason] = useState("");

    const yearOptions = useMemo(() => {
        const years = new Set<number>();
        allPeriodStatusRows.forEach((row) => years.add(row.fiscal_year));
        if (!years.size) {
            years.add(new Date().getFullYear());
        }
        return Array.from(years).sort((a, b) => b - a);
    }, [allPeriodStatusRows]);

    const periodsForTrialYear = useMemo(
        () => allPeriodStatusRows.filter((row) => row.fiscal_year === trialYear),
        [allPeriodStatusRows, trialYear],
    );

    const periodsForJournalYear = useMemo(
        () => allPeriodStatusRows.filter((row) => row.fiscal_year === journalYear),
        [allPeriodStatusRows, journalYear],
    );

    const selectedImportRow = useMemo(
        () => approvalQueue.find((row) => row.recid === selectedImport) ?? null,
        [approvalQueue, selectedImport],
    );

    const selectedPendingJournalRow = useMemo(
        () => pendingJournals.find((row) => row.recid === selectedPendingJournal) ?? null,
        [pendingJournals, selectedPendingJournal],
    );

    const loadApprovalQueue = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ imports: StagingImport[] }>("urn:finance:staging:list_imports:1", { status: 4 });
        setApprovalQueue(res.imports || []);
    }, []);

    const loadImportLineItems = useCallback(async (importsRecid: number): Promise<void> => {
        const res = await rpcCall<{ line_items: StagingLineItem[] }>("urn:finance:staging:list_line_items:1", {
            imports_recid: importsRecid,
        });
        setApprovalLineItems(res.line_items || []);
    }, []);

    const loadAllPeriodStatus = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ periods: PeriodStatus[] }>("urn:finance:reporting:period_status:1", {});
        setAllPeriodStatusRows(res.periods || []);
    }, []);

    const loadPeriodStatus = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ periods: PeriodStatus[] }>("urn:finance:reporting:period_status:1", {
            fiscal_year: periodYear || null,
        });
        setPeriodStatusRows(res.periods || []);
    }, [periodYear]);

    const loadTrialBalance = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ rows: TrialBalanceRow[] }>("urn:finance:reporting:trial_balance:1", {
            fiscal_year: trialYear || null,
            period_guid: trialPeriodGuid || null,
        });
        setTrialRows(res.rows || []);
    }, [trialPeriodGuid, trialYear]);

    const loadJournalSummary = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ journals: JournalSummaryRow[] }>("urn:finance:reporting:journal_summary:1", {
            journal_status: journalStatus === "" ? null : Number(journalStatus),
            fiscal_year: journalYear || null,
            periods_guid: journalPeriodGuid || null,
        });
        setJournalRows(res.journals || []);
    }, [journalPeriodGuid, journalStatus, journalYear]);

    const loadPendingJournals = useCallback(async (): Promise<void> => {
        const res = await rpcCall<{ journals: JournalSummaryRow[] }>("urn:finance:reporting:journal_summary:1", {
            journal_status: 1,
            fiscal_year: null,
            periods_guid: null,
        });
        setPendingJournals(res.journals || []);
    }, []);

    const loadPendingJournalLines = useCallback(async (recid: number): Promise<void> => {
        const res = await rpcCall<{ lines: JournalLine[] }>("urn:finance:journals:get_lines:1", { journals_recid: recid });
        setPendingJournalLines(res.lines || []);
    }, []);

    const loadAll = useCallback(async (): Promise<void> => {
        try {
            await Promise.all([loadApprovalQueue(), loadAllPeriodStatus(), loadPeriodStatus()]);
            setForbidden(false);
        } catch (error: any) {
            if (error?.response?.status === 403) {
                setForbidden(true);
                return;
            }
            throw error;
        }
    }, [loadAllPeriodStatus, loadApprovalQueue, loadPeriodStatus]);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    useEffect(() => {
        if (selectedImport === null) {
            setApprovalLineItems([]);
            return;
        }
        void loadImportLineItems(selectedImport);
    }, [loadImportLineItems, selectedImport]);

    useEffect(() => {
        if (selectedPendingJournal === null) {
            setPendingJournalLines([]);
            return;
        }
        void loadPendingJournalLines(selectedPendingJournal);
    }, [loadPendingJournalLines, selectedPendingJournal]);

    useEffect(() => {
        if (tab === 0) {
            void loadApprovalQueue();
        }
        if (tab === 1) {
            void loadPendingJournals();
        }
        if (tab === 2) {
            void loadPeriodStatus();
        }
        if (tab === 3) {
            void loadTrialBalance();
        }
        if (tab === 4) {
            void loadJournalSummary();
        }
    }, [tab, loadApprovalQueue, loadJournalSummary, loadPendingJournals, loadPeriodStatus, loadTrialBalance]);

    const trialTotals = useMemo(
        () => trialRows.reduce(
            (acc, row) => ({
                debit: acc.debit + Number(row.total_debit || 0),
                credit: acc.credit + Number(row.total_credit || 0),
                net: acc.net + Number(row.net_balance || 0),
            }),
            { debit: 0, credit: 0, net: 0 },
        ),
        [trialRows],
    );

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Access denied</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Accounting Manager</PageTitle>
            <Divider sx={{ mb: 2 }} />
            <Tabs value={tab} onChange={(_, next) => setTab(next)}>
                <Tab label="Approval Queue" />
                <Tab label="Journal Review" />
                <Tab label="Period Management" />
                <Tab label="Trial Balance" />
                <Tab label="Journal Summary" />
            </Tabs>

            {tab === 0 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle1">Imports Pending Approval</Typography>
                            <Button variant="outlined" onClick={() => void loadApprovalQueue()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>RecId</TableCell>
                                <TableCell>Source</TableCell>
                                <TableCell>Metric</TableCell>
                                <TableCell>Period</TableCell>
                                <TableCell>Rows</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Requested By</TableCell>
                                <TableCell>Approved By</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {approvalQueue.map((row) => {
                                const statusConfig = IMPORT_STATUS_CONFIG[row.element_status] || { label: String(row.element_status), color: "default" as const };
                                return (
                                    <TableRow
                                        hover
                                        key={row.recid}
                                        selected={selectedImport === row.recid}
                                        sx={{ cursor: "pointer" }}
                                        onClick={() => setSelectedImport(row.recid)}
                                    >
                                        <TableCell>{row.recid}</TableCell>
                                        <TableCell>{row.element_source}</TableCell>
                                        <TableCell>{row.element_metric}</TableCell>
                                        <TableCell>{row.element_period_start} → {row.element_period_end}</TableCell>
                                        <TableCell>{row.element_row_count}</TableCell>
                                        <TableCell><Chip label={statusConfig.label} color={statusConfig.color} /></TableCell>
                                        <TableCell>{row.element_requested_by || "-"}</TableCell>
                                        <TableCell>{row.element_approved_by || "-"}</TableCell>
                                        <TableCell onClick={(event) => event.stopPropagation()}>
                                            <Stack direction="row" spacing={1}>
                                                <Button
                                                    size="small"
                                                    variant="contained"
                                                    onClick={async () => {
                                                        await rpcCall("urn:finance:staging:approve:1", { imports_recid: row.recid });
                                                        await loadApprovalQueue();
                                                        if (selectedImport === row.recid) {
                                                            setSelectedImport(null);
                                                        }
                                                    }}
                                                >
                                                    Approve
                                                </Button>
                                                <Button
                                                    size="small"
                                                    color="error"
                                                    onClick={() => {
                                                        setSelectedImport(row.recid);
                                                        setRejectImportReason("");
                                                        setRejectImportDialogOpen(true);
                                                    }}
                                                >
                                                    Reject
                                                </Button>
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                    {selectedImportRow && (
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" sx={{ mb: 1 }}>
                                Import Line Items — #{selectedImportRow.recid}
                            </Typography>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Date</TableCell>
                                        <TableCell>Vendor</TableCell>
                                        <TableCell>Service</TableCell>
                                        <TableCell>Category</TableCell>
                                        <TableCell>Description</TableCell>
                                        <TableCell>Amount</TableCell>
                                        <TableCell>Currency</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {approvalLineItems.map((item) => (
                                        <TableRow key={item.recid}>
                                            <TableCell>{item.element_date || "-"}</TableCell>
                                            <TableCell>{item.vendor_name || "-"}</TableCell>
                                            <TableCell>{item.element_service || "-"}</TableCell>
                                            <TableCell>{item.element_category || "-"}</TableCell>
                                            <TableCell>{item.element_description || "-"}</TableCell>
                                            <TableCell>{item.element_amount}</TableCell>
                                            <TableCell>{item.element_currency || "-"}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </Paper>
                    )}
                </Stack>
            )}

            {tab === 1 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle1">Journals Pending Approval</Typography>
                            <Button variant="outlined" onClick={() => void loadPendingJournals()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>RecId</TableCell>
                                <TableCell>Posting Key</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Period</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Lines</TableCell>
                                <TableCell>Total Debit</TableCell>
                                <TableCell>Total Credit</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {pendingJournals.map((row) => {
                                const statusConfig = JOURNAL_STATUS_CONFIG[row.journal_status] || { label: String(row.journal_status), color: "warning" as const };
                                return (
                                    <TableRow
                                        hover
                                        key={row.recid}
                                        selected={selectedPendingJournal === row.recid}
                                        sx={{ cursor: "pointer" }}
                                        onClick={() => setSelectedPendingJournal(row.recid)}
                                    >
                                        <TableCell>{row.recid}</TableCell>
                                        <TableCell>{row.posting_key || "-"}</TableCell>
                                        <TableCell>{row.journal_name}</TableCell>
                                        <TableCell>{row.period_name || "-"}</TableCell>
                                        <TableCell><Chip label={statusConfig.label} color={statusConfig.color} /></TableCell>
                                        <TableCell>{row.line_count}</TableCell>
                                        <TableCell>{Number(row.total_debit || 0).toFixed(2)}</TableCell>
                                        <TableCell>{Number(row.total_credit || 0).toFixed(2)}</TableCell>
                                        <TableCell onClick={(event) => event.stopPropagation()}>
                                            <Stack direction="row" spacing={1}>
                                                <Button
                                                    size="small"
                                                    variant="contained"
                                                    onClick={async () => {
                                                        await rpcCall("urn:finance:journals:approve:1", { recid: row.recid });
                                                        await Promise.all([loadPendingJournals(), loadJournalSummary(), loadPeriodStatus()]);
                                                        if (selectedPendingJournal === row.recid) {
                                                            setSelectedPendingJournal(null);
                                                        }
                                                    }}
                                                >
                                                    Approve
                                                </Button>
                                                <Button
                                                    size="small"
                                                    color="error"
                                                    onClick={() => {
                                                        setSelectedPendingJournal(row.recid);
                                                        setRejectJournalReason("");
                                                        setRejectJournalDialogOpen(true);
                                                    }}
                                                >
                                                    Reject
                                                </Button>
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                    {selectedPendingJournalRow && (
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" sx={{ mb: 1 }}>
                                Journal Lines — #{selectedPendingJournalRow.recid}
                            </Typography>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Line</TableCell>
                                        <TableCell>Account</TableCell>
                                        <TableCell>Description</TableCell>
                                        <TableCell>Debit</TableCell>
                                        <TableCell>Credit</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {pendingJournalLines.map((line) => (
                                        <TableRow key={line.recid}>
                                            <TableCell>{line.line_number}</TableCell>
                                            <TableCell>{line.accounts_guid}</TableCell>
                                            <TableCell>{line.description || "-"}</TableCell>
                                            <TableCell>{Number(line.debit || 0).toFixed(2)}</TableCell>
                                            <TableCell>{Number(line.credit || 0).toFixed(2)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </Paper>
                    )}
                </Stack>
            )}

            {tab === 2 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <TextField
                                select
                                label="Fiscal Year"
                                value={periodYear}
                                onChange={(event) => setPeriodYear(Number(event.target.value))}
                                sx={{ minWidth: 140 }}
                            >
                                {yearOptions.map((year) => (
                                    <MenuItem key={year} value={year}>{year}</MenuItem>
                                ))}
                            </TextField>
                            <Button variant="outlined" onClick={() => void loadPeriodStatus()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Period</TableCell>
                                <TableCell>Start</TableCell>
                                <TableCell>End</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Total</TableCell>
                                <TableCell>Draft</TableCell>
                                <TableCell>Pending</TableCell>
                                <TableCell>Posted</TableCell>
                                <TableCell>Reversed</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {periodStatusRows.map((row) => (
                                <TableRow key={row.period_guid}>
                                    <TableCell>{row.period_name}</TableCell>
                                    <TableCell>{row.start_date}</TableCell>
                                    <TableCell>{row.end_date}</TableCell>
                                    <TableCell>
                                        <Chip
                                            label={PERIOD_STATUS_CONFIG[row.period_status]?.label || row.period_status}
                                            color={getPeriodChipColor(row)}
                                        />
                                    </TableCell>
                                    <TableCell>{row.total_journals}</TableCell>
                                    <TableCell>{row.draft_journals}</TableCell>
                                    <TableCell>{row.pending_journals}</TableCell>
                                    <TableCell>{row.posted_journals}</TableCell>
                                    <TableCell>{row.reversed_journals}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 3 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <TextField
                                select
                                label="Fiscal Year"
                                value={trialYear}
                                onChange={(event) => setTrialYear(Number(event.target.value))}
                                sx={{ minWidth: 140 }}
                            >
                                {yearOptions.map((year) => (
                                    <MenuItem key={year} value={year}>{year}</MenuItem>
                                ))}
                            </TextField>
                            <TextField
                                select
                                label="Period"
                                value={trialPeriodGuid}
                                onChange={(event) => setTrialPeriodGuid(event.target.value)}
                                sx={{ minWidth: 220 }}
                            >
                                <MenuItem value="">All</MenuItem>
                                {periodsForTrialYear.map((period) => (
                                    <MenuItem key={period.period_guid} value={period.period_guid}>
                                        FY{period.fiscal_year} - {period.period_name}
                                    </MenuItem>
                                ))}
                            </TextField>
                            <Button variant="outlined" onClick={() => void loadTrialBalance()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Account</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Debit</TableCell>
                                <TableCell>Credit</TableCell>
                                <TableCell>Net</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {trialRows.map((row) => (
                                <TableRow key={`${row.period_guid}-${row.account_guid}`}>
                                    <TableCell>{row.account_number}</TableCell>
                                    <TableCell>{row.account_name}</TableCell>
                                    <TableCell>{Number(row.total_debit || 0).toFixed(2)}</TableCell>
                                    <TableCell>{Number(row.total_credit || 0).toFixed(2)}</TableCell>
                                    <TableCell>{Number(row.net_balance || 0).toFixed(2)}</TableCell>
                                </TableRow>
                            ))}
                            <TableRow>
                                <TableCell colSpan={2}><strong>Total</strong></TableCell>
                                <TableCell><strong>{trialTotals.debit.toFixed(2)}</strong></TableCell>
                                <TableCell><strong>{trialTotals.credit.toFixed(2)}</strong></TableCell>
                                <TableCell><strong>{trialTotals.net.toFixed(2)}</strong></TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 4 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <TextField
                                select
                                label="Fiscal Year"
                                value={journalYear}
                                onChange={(event) => setJournalYear(Number(event.target.value))}
                                sx={{ minWidth: 140 }}
                            >
                                {yearOptions.map((year) => (
                                    <MenuItem key={year} value={year}>{year}</MenuItem>
                                ))}
                            </TextField>
                            <TextField
                                select
                                label="Period"
                                value={journalPeriodGuid}
                                onChange={(event) => setJournalPeriodGuid(event.target.value)}
                                sx={{ minWidth: 220 }}
                            >
                                <MenuItem value="">All</MenuItem>
                                {periodsForJournalYear.map((period) => (
                                    <MenuItem key={period.period_guid} value={period.period_guid}>
                                        FY{period.fiscal_year} - {period.period_name}
                                    </MenuItem>
                                ))}
                            </TextField>
                            <TextField
                                select
                                label="Status"
                                value={journalStatus}
                                onChange={(event) => setJournalStatus(event.target.value)}
                                sx={{ minWidth: 160 }}
                            >
                                <MenuItem value="">All</MenuItem>
                                <MenuItem value="0">Draft</MenuItem>
                                <MenuItem value="1">Pending</MenuItem>
                                <MenuItem value="2">Posted</MenuItem>
                                <MenuItem value="3">Reversed</MenuItem>
                            </TextField>
                            <Button variant="outlined" onClick={() => void loadJournalSummary()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>RecId</TableCell>
                                <TableCell>Posting Key</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Period</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Lines</TableCell>
                                <TableCell>Total Debit</TableCell>
                                <TableCell>Total Credit</TableCell>
                                <TableCell>Posted By</TableCell>
                                <TableCell>Posted On</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {journalRows.map((row) => {
                                const statusConfig = JOURNAL_STATUS_CONFIG[row.journal_status] || { label: String(row.journal_status), color: "warning" as const };
                                return (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.recid}</TableCell>
                                        <TableCell>{row.posting_key || "-"}</TableCell>
                                        <TableCell>{row.journal_name}</TableCell>
                                        <TableCell>{row.period_name || "-"}</TableCell>
                                        <TableCell><Chip label={statusConfig.label} color={statusConfig.color} /></TableCell>
                                        <TableCell>{row.line_count}</TableCell>
                                        <TableCell>{Number(row.total_debit || 0).toFixed(2)}</TableCell>
                                        <TableCell>{Number(row.total_credit || 0).toFixed(2)}</TableCell>
                                        <TableCell>{row.posted_by || "-"}</TableCell>
                                        <TableCell>{row.posted_on || "-"}</TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            <Dialog open={rejectImportDialogOpen} onClose={() => setRejectImportDialogOpen(false)} fullWidth maxWidth="sm">
                <DialogTitle>Reject Import</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        fullWidth
                        multiline
                        minRows={3}
                        label="Reason"
                        value={rejectImportReason}
                        onChange={(event) => setRejectImportReason(event.target.value)}
                        sx={{ mt: 1 }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRejectImportDialogOpen(false)}>Cancel</Button>
                    <Button
                        color="error"
                        variant="contained"
                        disabled={selectedImport === null}
                        onClick={async () => {
                            if (selectedImport === null) {
                                return;
                            }
                            await rpcCall("urn:finance:staging:reject:1", {
                                imports_recid: selectedImport,
                                reason: rejectImportReason || null,
                            });
                            setRejectImportDialogOpen(false);
                            setSelectedImport(null);
                            await loadApprovalQueue();
                        }}
                    >
                        Reject
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={rejectJournalDialogOpen} onClose={() => setRejectJournalDialogOpen(false)} fullWidth maxWidth="sm">
                <DialogTitle>Reject Journal</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        fullWidth
                        multiline
                        minRows={3}
                        label="Reason"
                        value={rejectJournalReason}
                        onChange={(event) => setRejectJournalReason(event.target.value)}
                        sx={{ mt: 1 }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setRejectJournalDialogOpen(false)}>Cancel</Button>
                    <Button
                        color="error"
                        variant="contained"
                        disabled={selectedPendingJournal === null}
                        onClick={async () => {
                            if (selectedPendingJournal === null) {
                                return;
                            }
                            await rpcCall("urn:finance:journals:reject:1", {
                                recid: selectedPendingJournal,
                                reason: rejectJournalReason || null,
                            });
                            setRejectJournalDialogOpen(false);
                            setSelectedPendingJournal(null);
                            await Promise.all([loadPendingJournals(), loadJournalSummary()]);
                        }}
                    >
                        Reject
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default FinanceManagerPage;
