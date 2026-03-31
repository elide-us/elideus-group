import { useCallback, useEffect, useMemo, useState } from "react";
import {
    Alert,
    Box,
    Button,
    Chip,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    LinearProgress,
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
import Notification from "../../components/Notification";
import PageTitle from "../../components/PageTitle";
import { fetchList as fetchPeriodsList, fetchListCloseBlockers } from '../../rpc/finance/periods';
import { fetchList as fetchAccountsList } from '../../rpc/finance/accounts';
import { fetchList as fetchLedgersList } from '../../rpc/finance/ledgers';
import { fetchList as fetchNumbersList, fetchUpsert as fetchUpsertNumber, fetchDelete as fetchDeleteNumber, fetchNextNumber } from '../../rpc/finance/numbers';
import { fetchJournalSummary, fetchCreditLotSummary } from '../../rpc/finance/reporting';
import { fetchListImports, fetchListLineItems, fetchImport as fetchStagingImport, fetchImportInvoices, fetchDeleteImport, fetchPromote } from '../../rpc/finance/staging';
import { fetchCreate as fetchJournalCreate, fetchLines as fetchJournalLines, fetchSubmitForApproval, fetchReverse as fetchJournalReverse } from '../../rpc/finance/journals';
import { fetchCreate as fetchCreditLotCreate, fetchExpire as fetchCreditLotExpire, fetchListEvents as fetchCreditLotEvents } from '../../rpc/finance/credit_lots';
import { fetchGet as fetchScheduledTaskGet } from '../../rpc/system/scheduled_tasks';

type FinanceNumber = {
    recid?: number | null;
    accounts_guid: string;
    prefix?: string | null;
    account_number: string;
    last_number: number;
    allocation_size: number;
    reset_policy: string;
    account_name?: string | null;
};

type FinanceAccount = {
    guid: string;
    number: string;
    name: string;
    is_posting: boolean;
};

type FinanceLedger = {
    recid: number;
    element_name: string;
};

type FinancePeriod = {
    guid: string;
    year: number;
    period_number: number;
    period_name: string;
    status: number;
    closed_by?: string | null;
    closed_on?: string | null;
    locked_by?: string | null;
    locked_on?: string | null;
};

type PeriodCloseBlocker = {
    period_guid: string;
    blocker_type: string;
    blocker_recid: number;
    blocker_name: string;
    blocker_reason: string;
};

type JournalSummaryRow = {
    recid: number;
    posting_key: string;
    journal_name: string;
    source_type: string;
    period_name: string;
    journal_status: number;
    line_count: number;
    total_debit: string;
    total_credit: string;
    posted_by: string | null;
    posted_on?: string | null;
    created_on: string;
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

type JournalCreateLine = {
    line_number: number;
    accounts_guid: string;
    debit: string;
    credit: string;
    description: string | null;
    dimension_recids: number[];
};

type JournalCreateForm = {
    name: string;
    description: string | null;
    posting_key: string | null;
    source_type: string | null;
    source_id: string | null;
    periods_guid: string | null;
    ledgers_recid: number | null;
    lines: JournalCreateLine[];
};

type CreditLotSummaryRow = {
    recid: number;
    lot_number: string;
    users_guid: string;
    source_type: string;
    credits_original: number;
    credits_remaining: number;
    unit_price: string;
    total_paid: string;
    expired: boolean;
    event_count: number;
    total_consumed: number;
    created_on: string;
};

type CreditLotEvent = {
    recid: number;
    event_type: string;
    credits: number;
    unit_price: string;
    description: string | null;
    actor_guid: string | null;
    journals_recid: number | null;
};

type CreditLotCreateForm = {
    users_guid: string;
    source_type: string;
    credits: number;
    total_paid: string;
    currency: string;
    expires_at: string | null;
    source_id: string | null;
};

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
    element_requested_by: string | null;
    element_approved_by: string | null;
    element_approved_on: string | null;
    element_created_on: string;
};

type StagingLineItem = {
    recid: number;
    imports_recid: number;
    vendor_name: string | null;
    element_date: string | null;
    element_service: string | null;
    element_category: string | null;
    element_description: string | null;
    element_amount: string;
    element_currency: string | null;
};

type AsyncTask = {
    guid: string;
    status: number;
    handler_name: string | null;
    current_step: string | null;
    step_index: number | null;
    step_count: number | null;
    result: Record<string, any> | null;
    error: string | null;
};

type AsyncTaskEvent = Record<string, any>;

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

const PROMOTE_PIPELINE_STEPS = ["validate_import", "classify_costs", "create_journal", "mark_promoted"] as const;

const DEFAULT_JOURNAL_LINE = (lineNumber: number): JournalCreateLine => ({
    line_number: lineNumber,
    accounts_guid: "",
    debit: "0",
    credit: "0",
    description: "",
    dimension_recids: [],
});


const getErrorMessage = (error: unknown): string => {
    if (typeof error === "object" && error !== null) {
        const response = Reflect.get(error, "response");
        if (typeof response === "object" && response !== null) {
            const data = Reflect.get(response, "data");
            if (typeof data === "object" && data !== null) {
                const detail = Reflect.get(data, "detail");
                if (typeof detail === "string" && detail.trim()) {
                    return detail;
                }
            }
        }
        const message = Reflect.get(error, "message");
        if (typeof message === "string" && message.trim()) {
            return message;
        }
    }
    return "Something went wrong.";
};

const FinanceAccountantPage = (): JSX.Element => {
    const [tab, setTab] = useState(0);
    const [forbidden, setForbidden] = useState(false);

    const [periods, setPeriods] = useState<FinancePeriod[]>([]);
    const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
    const [ledgers, setLedgers] = useState<FinanceLedger[]>([]);
    const [numbers, setNumbers] = useState<FinanceNumber[]>([]);

    const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
    const [selectedPeriodGuid, setSelectedPeriodGuid] = useState<string>("");
    const [selectedReadinessPeriodGuid, setSelectedReadinessPeriodGuid] = useState<string>("");
    const [closeBlockers, setCloseBlockers] = useState<PeriodCloseBlocker[]>([]);
    const [readinessLoading, setReadinessLoading] = useState(false);
    const [readinessError, setReadinessError] = useState<string | null>(null);
    const [journalStatus, setJournalStatus] = useState<string>("");
    const [journals, setJournals] = useState<JournalSummaryRow[]>([]);
    const [journalLines, setJournalLines] = useState<JournalLine[]>([]);
    const [selectedJournal, setSelectedJournal] = useState<JournalSummaryRow | null>(null);
    const [journalDialogOpen, setJournalDialogOpen] = useState(false);
    const [createJournalOpen, setCreateJournalOpen] = useState(false);
    const [journalForm, setJournalForm] = useState<JournalCreateForm>({
        name: "",
        description: null,
        posting_key: null,
        source_type: "manual",
        source_id: null,
        periods_guid: null,
        ledgers_recid: null,
        lines: [DEFAULT_JOURNAL_LINE(1)],
    });

    const [lotUserGuid, setLotUserGuid] = useState("");
    const [lots, setLots] = useState<CreditLotSummaryRow[]>([]);
    const [lotEvents, setLotEvents] = useState<CreditLotEvent[]>([]);
    const [lotDialogOpen, setLotDialogOpen] = useState(false);
    const [grantDialogOpen, setGrantDialogOpen] = useState(false);
    const [grantForm, setGrantForm] = useState<CreditLotCreateForm>({
        users_guid: "",
        source_type: "grant_owner",
        credits: 0,
        total_paid: "0",
        currency: "USD",
        expires_at: null,
        source_id: null,
    });

    const [numberForm, setNumberForm] = useState<FinanceNumber>({
        recid: null,
        accounts_guid: "",
        prefix: "",
        account_number: "",
        last_number: 1000,
        allocation_size: 10,
        reset_policy: "Never",
    });

    const [importStartDate, setImportStartDate] = useState("");
    const [importEndDate, setImportEndDate] = useState("");
    const [invoiceMonth, setInvoiceMonth] = useState("");
    const [invoiceMonthOrg, setInvoiceMonthOrg] = useState("");
    const [billingImports, setBillingImports] = useState<StagingImport[]>([]);
    const [selectedBillingImport, setSelectedBillingImport] = useState<number | null>(null);
    const [billingLineItems, setBillingLineItems] = useState<StagingLineItem[]>([]);
    const [importing, setImporting] = useState(false);
    const [importingInvoices, setImportingInvoices] = useState(false);
    const [importingInvoicesOrg, setImportingInvoicesOrg] = useState(false);
    const [billingMessage, setBillingMessage] = useState<{ severity: "success" | "error" | "info"; text: string } | null>(null);

    const [approvedImports, setApprovedImports] = useState<StagingImport[]>([]);
    const [selectedApprovedImport, setSelectedApprovedImport] = useState<number | null>(null);
    const [approvedLineItems, setApprovedLineItems] = useState<StagingLineItem[]>([]);
    const [selectedLedgerRecid, setSelectedLedgerRecid] = useState<number | null>(null);
    const [promoteTaskGuid, setPromoteTaskGuid] = useState<string | null>(null);
    const [promoteTaskStatus, setPromoteTaskStatus] = useState<AsyncTask | null>(null);
    const [promoteTaskEvents, setPromoteTaskEvents] = useState<AsyncTaskEvent[]>([]);

    const [notification, setNotification] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState("Done");
    const [notificationSeverity, setNotificationSeverity] = useState<"success" | "error">("success");

    const showNotification = (message: string, severity: "success" | "error" = "success"): void => {
        setNotificationMessage(message);
        setNotificationSeverity(severity);
        setNotification(true);
    };

    const fiscalYears = useMemo(() => {
        const years = new Set<number>();
        periods.forEach((period) => years.add(period.year));
        if (!years.size) {
            years.add(new Date().getFullYear());
        }
        return Array.from(years).sort((a, b) => b - a);
    }, [periods]);

    const periodsForSelectedYear = useMemo(
        () => periods.filter((period) => period.year === selectedYear),
        [periods, selectedYear],
    );

    const openPeriodsForSelectedYear = useMemo(
        () => periodsForSelectedYear.filter((period) => period.status === 1),
        [periodsForSelectedYear],
    );

    const selectedReadinessPeriod = useMemo(
        () => openPeriodsForSelectedYear.find((period) => period.guid === selectedReadinessPeriodGuid) ?? null,
        [openPeriodsForSelectedYear, selectedReadinessPeriodGuid],
    );

    const postingAccounts = useMemo(
        () => accounts.filter((account) => account.is_posting),
        [accounts],
    );

    const selectedBillingImportRow = useMemo(
        () => billingImports.find((item) => item.recid === selectedBillingImport) ?? null,
        [billingImports, selectedBillingImport],
    );

    const selectedApprovedImportRow = useMemo(
        () => approvedImports.find((item) => item.recid === selectedApprovedImport) ?? null,
        [approvedImports, selectedApprovedImport],
    );

    const loadShared = useCallback(async (): Promise<void> => {
        const [periodRes, accountRes, ledgerRes, numberRes] = await Promise.all([
            fetchPeriodsList() as any,
            fetchAccountsList() as any,
            fetchLedgersList() as any,
            fetchNumbersList() as any,
        ]);
        setPeriods(periodRes.periods || []);
        setAccounts(accountRes.accounts || []);
        setLedgers(ledgerRes.ledgers || []);
        setNumbers(numberRes.numbers || []);
    }, []);

    const loadJournals = useCallback(async (): Promise<void> => {
        const res = await fetchJournalSummary({
            journal_status: journalStatus === "" ? null : Number(journalStatus),
            fiscal_year: selectedYear || null,
            periods_guid: selectedPeriodGuid || null,
        }) as any;
        setJournals(res.journals || []);
    }, [journalStatus, selectedPeriodGuid, selectedYear]);

    const loadLots = useCallback(async (): Promise<void> => {
        const res = await fetchCreditLotSummary({
            users_guid: lotUserGuid || null,
        }) as any;
        setLots(res.lots || []);
    }, [lotUserGuid]);

    const loadBillingImports = useCallback(async (): Promise<void> => {
        const res = await fetchListImports({}) as any;
        setBillingImports(res.imports || []);
    }, []);

    const loadApprovedImports = useCallback(async (): Promise<void> => {
        const res = await fetchListImports({ status: 1 }) as any;
        setApprovedImports(res.imports || []);
    }, []);

    const loadLineItems = useCallback(async (importsRecid: number, setter: (items: StagingLineItem[]) => void): Promise<void> => {
        const res = await fetchListLineItems({
            imports_recid: importsRecid,
        }) as any;
        setter(res.line_items || []);
    }, []);

    const loadTaskEvents = useCallback(async (guid: string): Promise<void> => {
        // TODO: system:tasks:events not yet available as generated wrapper
        const res = await fetchScheduledTaskGet({ guid }) as any;
        setPromoteTaskEvents(res.events || []);
    }, []);

    const loadCloseReadiness = useCallback(async (guid: string): Promise<void> => {
        setSelectedReadinessPeriodGuid(guid);
        setReadinessLoading(true);
        setReadinessError(null);
        try {
            const res = await fetchListCloseBlockers({ guid }) as any;
            setCloseBlockers(res.blockers || []);
        } catch (error: unknown) {
            setCloseBlockers([]);
            setReadinessError(getErrorMessage(error));
        } finally {
            setReadinessLoading(false);
        }
    }, []);

    useEffect(() => {
        void (async () => {
            try {
                await loadShared();
                setForbidden(false);
            } catch (error: any) {
                if (error?.response?.status === 403) {
                    setForbidden(true);
                    return;
                }
                throw error;
            }
        })();
    }, [loadShared]);

    useEffect(() => {
        if (tab === 0) {
            void loadBillingImports();
        }
        if (tab === 1) {
            void loadApprovedImports();
        }
        if (tab === 2) {
            setReadinessError(null);
        }
        if (tab === 3) {
            void loadJournals();
        }
        if (tab === 4) {
            void loadLots();
        }
        if (tab === 5) {
            void loadShared();
        }
    }, [tab, loadApprovedImports, loadBillingImports, loadJournals, loadLots, loadShared]);

    useEffect(() => {
        if (selectedBillingImport === null) {
            setBillingLineItems([]);
            return;
        }
        void loadLineItems(selectedBillingImport, setBillingLineItems);
    }, [loadLineItems, selectedBillingImport]);

    useEffect(() => {
        if (selectedApprovedImport === null) {
            setApprovedLineItems([]);
            return;
        }
        void loadLineItems(selectedApprovedImport, setApprovedLineItems);
    }, [loadLineItems, selectedApprovedImport]);

    useEffect(() => {
        if (!promoteTaskGuid || tab !== 1) {
            return;
        }

        let active = true;
        let intervalId = 0;

        const pollTask = async (): Promise<void> => {
            try {
                const task = await fetchScheduledTaskGet({ guid: promoteTaskGuid }) as any;
                if (!active) {
                    return;
                }
                setPromoteTaskStatus(task);
                await loadTaskEvents(promoteTaskGuid);
                if (!active) {
                    return;
                }
                if (task.status === 4) {
                    window.clearInterval(intervalId);
                    const journalRecid = task.result?.journal_recid ?? task.result?.journals_recid;
                    showNotification(journalRecid ? `Promotion completed — journal #${journalRecid}` : "Promotion completed.");
                    await Promise.all([loadApprovedImports(), loadBillingImports(), loadJournals()]);
                    return;
                }
                if (task.status >= 5) {
                    window.clearInterval(intervalId);
                    showNotification(task.error || "Promotion failed.", "error");
                }
            } catch (error: any) {
                if (!active) {
                    return;
                }
                if ((error?.response?.status ?? error?.status) !== 404) {
                    showNotification(error?.message || "Unable to monitor promotion task.", "error");
                }
            }
        };

        void pollTask();
        intervalId = window.setInterval(() => void pollTask(), 4000);

        return () => {
            active = false;
            window.clearInterval(intervalId);
        };
    }, [loadApprovedImports, loadBillingImports, loadJournals, loadTaskEvents, promoteTaskGuid, tab]);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Access denied</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Accountant</PageTitle>
            <Divider sx={{ mb: 2 }} />
            <Tabs value={tab} onChange={(_, next) => setTab(next)}>
                <Tab label="Billing Import" />
                <Tab label="Staging Review" />
                <Tab label="Period Close" />
                <Tab label="Journals" />
                <Tab label="Credit Lots" />
                <Tab label="Number Sequences" />
            </Tabs>

            {tab === 0 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                <TextField label="Start Date (YYYY-MM-DD)" value={importStartDate} onChange={(e) => setImportStartDate(e.target.value)} />
                                <TextField label="End Date (YYYY-MM-DD)" value={importEndDate} onChange={(e) => setImportEndDate(e.target.value)} />
                                <Button
                                    variant="contained"
                                    disabled={importing}
                                    onClick={async () => {
                                        setImporting(true);
                                        setBillingMessage(null);
                                        try {
                                            await fetchStagingImport({ period_start: importStartDate, period_end: importEndDate });
                                            setBillingMessage({ severity: "success", text: "Cost detail import started successfully." });
                                            await loadBillingImports();
                                        } catch (error: any) {
                                            setBillingMessage({ severity: "error", text: error?.message || "Cost detail import failed." });
                                        } finally {
                                            setImporting(false);
                                        }
                                    }}
                                >
                                    {importing ? "Importing..." : "Import Cost Details"}
                                </Button>
                            </Stack>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                <TextField label="PAYG Invoice Month (YYYY-MM)" value={invoiceMonth} onChange={(e) => setInvoiceMonth(e.target.value)} />
                                <Button
                                    variant="contained"
                                    disabled={importingInvoices}
                                    onClick={async () => {
                                        setImportingInvoices(true);
                                        setBillingMessage(null);
                                        try {
                                            const res = await fetchImportInvoices({ period_month: invoiceMonth }) as any;
                                            setBillingMessage({ severity: "success", text: res.message || "PAYG invoice import completed." });
                                            await loadBillingImports();
                                        } catch (error: any) {
                                            setBillingMessage({ severity: "error", text: error?.message || "PAYG invoice import failed." });
                                        } finally {
                                            setImportingInvoices(false);
                                        }
                                    }}
                                >
                                    {importingInvoices ? "Importing..." : "Import PAYG Invoices"}
                                </Button>
                            </Stack>
                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                <TextField label="Org Invoice Month (YYYY-MM)" value={invoiceMonthOrg} onChange={(e) => setInvoiceMonthOrg(e.target.value)} />
                                <Button
                                    variant="contained"
                                    disabled={importingInvoicesOrg}
                                    onClick={async () => {
                                        setImportingInvoicesOrg(true);
                                        setBillingMessage(null);
                                        try {
                                            const res = await fetchImportInvoices({
                                                period_month: invoiceMonthOrg,
                                                billing_account: "org",
                                            });
                                            setBillingMessage({ severity: "success", text: res.message || "Org invoice import completed." });
                                            await loadBillingImports();
                                        } catch (error: any) {
                                            setBillingMessage({ severity: "error", text: error?.message || "Org invoice import failed." });
                                        } finally {
                                            setImportingInvoicesOrg(false);
                                        }
                                    }}
                                >
                                    {importingInvoicesOrg ? "Importing..." : "Import Org Invoices"}
                                </Button>
                            </Stack>
                            {billingMessage && <Alert severity={billingMessage.severity}>{billingMessage.text}</Alert>}
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>RecId</TableCell>
                                <TableCell>Source</TableCell>
                                <TableCell>Metric</TableCell>
                                <TableCell>Period Start</TableCell>
                                <TableCell>Period End</TableCell>
                                <TableCell>Rows</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Requested By</TableCell>
                                <TableCell>Approved By</TableCell>
                                <TableCell>Created</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {billingImports.map((row) => {
                                const statusConfig = IMPORT_STATUS_CONFIG[row.element_status] || { label: String(row.element_status), color: "default" as const };
                                return (
                                    <TableRow
                                        hover
                                        key={row.recid}
                                        selected={selectedBillingImport === row.recid}
                                        sx={{ cursor: "pointer" }}
                                        onClick={() => setSelectedBillingImport(row.recid)}
                                    >
                                        <TableCell>{row.recid}</TableCell>
                                        <TableCell>{row.element_source}</TableCell>
                                        <TableCell>{row.element_metric}</TableCell>
                                        <TableCell>{row.element_period_start}</TableCell>
                                        <TableCell>{row.element_period_end}</TableCell>
                                        <TableCell>{row.element_row_count}</TableCell>
                                        <TableCell><Chip label={statusConfig.label} color={statusConfig.color} /></TableCell>
                                        <TableCell>{row.element_requested_by || "-"}</TableCell>
                                        <TableCell>{row.element_approved_by || "-"}</TableCell>
                                        <TableCell>{row.element_created_on}</TableCell>
                                        <TableCell onClick={(event) => event.stopPropagation()}>
                                            {row.element_status !== 3 && (
                                                <Button
                                                    size="small"
                                                    color="error"
                                                    onClick={async () => {
                                                        if (!window.confirm(`Delete staging import #${row.recid}?`)) {
                                                            return;
                                                        }
                                                        await fetchDeleteImport({ imports_recid: row.recid });
                                                        if (selectedBillingImport === row.recid) {
                                                            setSelectedBillingImport(null);
                                                        }
                                                        await loadBillingImports();
                                                    }}
                                                >
                                                    Delete
                                                </Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                    {selectedBillingImportRow && (
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" sx={{ mb: 1 }}>Import Line Items — #{selectedBillingImportRow.recid}</Typography>
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
                                    {billingLineItems.map((item) => (
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
                        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <Button variant="outlined" onClick={() => void loadApprovedImports()}>Refresh</Button>
                            <TextField
                                select
                                label="Ledger"
                                value={selectedLedgerRecid ?? ""}
                                onChange={(event) => setSelectedLedgerRecid(event.target.value === "" ? null : Number(event.target.value))}
                                sx={{ minWidth: 220 }}
                            >
                                <MenuItem value="">Auto / None</MenuItem>
                                {ledgers.map((ledger) => (
                                    <MenuItem key={ledger.recid} value={ledger.recid}>{ledger.element_name}</MenuItem>
                                ))}
                            </TextField>
                            <Button
                                variant="contained"
                                disabled={selectedApprovedImport === null}
                                onClick={async () => {
                                    if (selectedApprovedImport === null) {
                                        return;
                                    }
                                    const res = await fetchPromote({
                                        imports_recid: selectedApprovedImport,
                                        ledgers_recid: selectedLedgerRecid,
                                    });
                                    setPromoteTaskGuid(res.task_guid);
                                    setPromoteTaskStatus(null);
                                    setPromoteTaskEvents([]);
                                }}
                            >
                                Promote Import
                            </Button>
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
                                <TableCell>Approved By</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {approvedImports.map((row) => (
                                <TableRow
                                    hover
                                    key={row.recid}
                                    selected={selectedApprovedImport === row.recid}
                                    sx={{ cursor: "pointer" }}
                                    onClick={() => setSelectedApprovedImport(row.recid)}
                                >
                                    <TableCell>{row.recid}</TableCell>
                                    <TableCell>{row.element_source}</TableCell>
                                    <TableCell>{row.element_metric}</TableCell>
                                    <TableCell>{row.element_period_start} → {row.element_period_end}</TableCell>
                                    <TableCell>{row.element_row_count}</TableCell>
                                    <TableCell><Chip label={IMPORT_STATUS_CONFIG[row.element_status]?.label || row.element_status} color={IMPORT_STATUS_CONFIG[row.element_status]?.color || "default"} /></TableCell>
                                    <TableCell>{row.element_approved_by || "-"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {selectedApprovedImportRow && (
                        <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" sx={{ mb: 1 }}>Approved Line Items — #{selectedApprovedImportRow.recid}</Typography>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Date</TableCell>
                                        <TableCell>Vendor</TableCell>
                                        <TableCell>Service</TableCell>
                                        <TableCell>Category</TableCell>
                                        <TableCell>Description</TableCell>
                                        <TableCell>Amount</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {approvedLineItems.map((item) => (
                                        <TableRow key={item.recid}>
                                            <TableCell>{item.element_date || "-"}</TableCell>
                                            <TableCell>{item.vendor_name || "-"}</TableCell>
                                            <TableCell>{item.element_service || "-"}</TableCell>
                                            <TableCell>{item.element_category || "-"}</TableCell>
                                            <TableCell>{item.element_description || "-"}</TableCell>
                                            <TableCell>{item.element_amount}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </Paper>
                    )}
                    {(promoteTaskGuid || promoteTaskStatus) && (
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Typography variant="subtitle1">Promotion Progress</Typography>
                                {promoteTaskStatus && (
                                    <>
                                        <Stack direction="row" spacing={1} alignItems="center">
                                            {(promoteTaskStatus.status === 0 || promoteTaskStatus.status === 1) ? <CircularProgress size={18} /> : null}
                                            <Typography>
                                                {promoteTaskStatus.current_step || "Queued"}
                                                {typeof promoteTaskStatus.step_index === "number" && typeof promoteTaskStatus.step_count === "number"
                                                    ? ` (${promoteTaskStatus.step_index + 1}/${promoteTaskStatus.step_count})`
                                                    : ""}
                                            </Typography>
                                        </Stack>
                                        {typeof promoteTaskStatus.step_index === "number" && typeof promoteTaskStatus.step_count === "number" && promoteTaskStatus.step_count > 0 && (
                                            <LinearProgress variant="determinate" value={((promoteTaskStatus.step_index + 1) / promoteTaskStatus.step_count) * 100} />
                                        )}
                                        {promoteTaskStatus.status === 4 && <Alert severity="success">Promotion complete.</Alert>}
                                        {promoteTaskStatus.status >= 5 && <Alert severity="error">{promoteTaskStatus.error || "Promotion failed."}</Alert>}
                                    </>
                                )}
                                <Stack spacing={1}>
                                    {PROMOTE_PIPELINE_STEPS.map((step) => {
                                        const activeStep = promoteTaskStatus?.current_step === step;
                                        const completed = promoteTaskEvents.some((event) => event.step_name === step && event.status === "completed");
                                        return (
                                            <Stack key={step} direction="row" spacing={1} alignItems="center">
                                                <Chip size="small" color={completed ? "success" : activeStep ? "info" : "default"} label={step} />
                                            </Stack>
                                        );
                                    })}
                                </Stack>
                            </Stack>
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
                                value={selectedYear}
                                onChange={(event) => setSelectedYear(Number(event.target.value))}
                                sx={{ minWidth: 120 }}
                            >
                                {fiscalYears.map((year) => (
                                    <MenuItem key={year} value={year}>{year}</MenuItem>
                                ))}
                            </TextField>
                            <Button variant="outlined" onClick={() => void loadShared()}>Refresh</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Period</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Closed</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {openPeriodsForSelectedYear.map((period) => (
                                <TableRow key={period.guid} selected={selectedReadinessPeriodGuid === period.guid}>
                                    <TableCell>{period.period_name}</TableCell>
                                    <TableCell><Chip color="success" label="Open" /></TableCell>
                                    <TableCell>{period.closed_on || "-"}</TableCell>
                                    <TableCell>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            onClick={() => void loadCloseReadiness(period.guid)}
                                        >
                                            Check Close Readiness
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {openPeriodsForSelectedYear.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={4}>No open periods for the selected fiscal year.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                    {selectedReadinessPeriod && (
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Typography variant="subtitle1">
                                    Close readiness — {selectedReadinessPeriod.period_name}
                                </Typography>
                                {readinessLoading && <CircularProgress size={24} />}
                                {readinessError && <Alert severity="error">{readinessError}</Alert>}
                                {!readinessLoading && !readinessError && closeBlockers.length === 0 && (
                                    <Alert severity="success">Ready for close.</Alert>
                                )}
                                {!readinessLoading && closeBlockers.length > 0 && (
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Type</TableCell>
                                                <TableCell>Name</TableCell>
                                                <TableCell>Reason</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {closeBlockers.map((blocker) => (
                                                <TableRow key={`${blocker.blocker_type}-${blocker.blocker_recid}`}>
                                                    <TableCell>{blocker.blocker_type}</TableCell>
                                                    <TableCell>{blocker.blocker_name}</TableCell>
                                                    <TableCell>{blocker.blocker_reason}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                )}
                            </Stack>
                        </Paper>
                    )}
                </Stack>
            )}

            {tab === 3 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField
                                select
                                label="Fiscal Year"
                                value={selectedYear}
                                onChange={(event) => setSelectedYear(Number(event.target.value))}
                                sx={{ minWidth: 120 }}
                            >
                                {fiscalYears.map((year) => (
                                    <MenuItem key={year} value={year}>{year}</MenuItem>
                                ))}
                            </TextField>
                            <TextField
                                select
                                label="Period"
                                value={selectedPeriodGuid}
                                onChange={(event) => setSelectedPeriodGuid(event.target.value)}
                                sx={{ minWidth: 220 }}
                            >
                                <MenuItem value="">All</MenuItem>
                                {periodsForSelectedYear.map((period) => (
                                    <MenuItem key={period.guid} value={period.guid}>FY{period.year} - {period.period_name}</MenuItem>
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
                            <Button variant="outlined" onClick={() => void loadJournals()}>Refresh</Button>
                            <Button variant="contained" onClick={() => setCreateJournalOpen(true)}>Create Journal</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Posting Key</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Source Type</TableCell>
                                <TableCell>Period</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Lines</TableCell>
                                <TableCell>Total Debit</TableCell>
                                <TableCell>Total Credit</TableCell>
                                <TableCell>Posted By</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {journals.map((row) => {
                                const statusConfig = JOURNAL_STATUS_CONFIG[row.journal_status] || { label: String(row.journal_status), color: "warning" as const };
                                return (
                                    <TableRow
                                        hover
                                        key={row.recid}
                                        sx={{ cursor: "pointer" }}
                                        onClick={async () => {
                                            const res = await fetchJournalLines({ journals_recid: row.recid }) as any;
                                            setJournalLines(res.lines || []);
                                            setSelectedJournal(row);
                                            setJournalDialogOpen(true);
                                        }}
                                    >
                                        <TableCell>{row.posting_key || "-"}</TableCell>
                                        <TableCell>{row.journal_name}</TableCell>
                                        <TableCell>{row.source_type}</TableCell>
                                        <TableCell>{row.period_name || "-"}</TableCell>
                                        <TableCell><Chip label={statusConfig.label} color={statusConfig.color} /></TableCell>
                                        <TableCell>{row.line_count}</TableCell>
                                        <TableCell>{Number(row.total_debit || 0).toFixed(2)}</TableCell>
                                        <TableCell>{Number(row.total_credit || 0).toFixed(2)}</TableCell>
                                        <TableCell>{row.posted_by || "-"}</TableCell>
                                        <TableCell onClick={(event) => event.stopPropagation()}>
                                            <Stack direction="row" spacing={1}>
                                                {row.journal_status === 0 && (
                                                    <Button
                                                        size="small"
                                                        variant="contained"
                                                        onClick={async () => {
                                                            await fetchSubmitForApproval({ recid: row.recid });
                                                            await loadJournals();
                                                        }}
                                                    >
                                                        Submit for Approval
                                                    </Button>
                                                )}
                                                {row.journal_status === 2 && row.source_type !== "reversal" && (
                                                    <Button
                                                        size="small"
                                                        color="error"
                                                        onClick={async () => {
                                                            if (!window.confirm("Reverse this journal?")) {
                                                                return;
                                                            }
                                                            await fetchJournalReverse({ recid: row.recid });
                                                            await loadJournals();
                                                        }}
                                                    >
                                                        Reverse
                                                    </Button>
                                                )}
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 4 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField label="User GUID (optional)" value={lotUserGuid} onChange={(event) => setLotUserGuid(event.target.value)} />
                            <Button variant="outlined" onClick={() => void loadLots()}>Refresh</Button>
                            <Button variant="contained" onClick={() => setGrantDialogOpen(true)}>Grant Credits</Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Lot Number</TableCell>
                                <TableCell>User</TableCell>
                                <TableCell>Source Type</TableCell>
                                <TableCell>Original</TableCell>
                                <TableCell>Remaining</TableCell>
                                <TableCell>Unit Price</TableCell>
                                <TableCell>Total Paid</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Events</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {lots.map((row) => (
                                <TableRow key={row.recid} hover sx={{ cursor: "pointer" }} onClick={async () => {
                                    const res = await fetchCreditLotEvents({ lots_recid: row.recid }) as any;
                                    setLotEvents(res.events || []);
                                    setLotDialogOpen(true);
                                }}>
                                    <TableCell>{row.lot_number}</TableCell>
                                    <TableCell>{row.users_guid}</TableCell>
                                    <TableCell>{row.source_type}</TableCell>
                                    <TableCell>{Number(row.credits_original || 0).toFixed(2)}</TableCell>
                                    <TableCell>{Number(row.credits_remaining || 0).toFixed(2)}</TableCell>
                                    <TableCell>{Number(row.unit_price || 0).toFixed(2)}</TableCell>
                                    <TableCell>{Number(row.total_paid || 0).toFixed(2)}</TableCell>
                                    <TableCell><Chip label={row.expired ? "Expired" : "Active"} color={row.expired ? "error" : "success"} /></TableCell>
                                    <TableCell>{row.event_count}</TableCell>
                                    <TableCell onClick={(event) => event.stopPropagation()}>
                                        {!row.expired && (
                                            <Button size="small" color="error" onClick={async () => {
                                                if (!window.confirm("Expire this credit lot?")) {
                                                    return;
                                                }
                                                await fetchCreditLotExpire({ recid: row.recid });
                                                await loadLots();
                                            }}>Expire</Button>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 5 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField label="Prefix" value={numberForm.prefix || ""} onChange={(event) => setNumberForm((prev) => ({ ...prev, prefix: event.target.value }))} />
                            <TextField
                                select
                                label="Account"
                                value={numberForm.accounts_guid}
                                onChange={(event) => setNumberForm((prev) => ({ ...prev, accounts_guid: event.target.value }))}
                                sx={{ minWidth: 280 }}
                            >
                                <MenuItem value="">Select account</MenuItem>
                                {accounts.map((account) => (
                                    <MenuItem key={account.guid} value={account.guid}>{account.number} — {account.name}</MenuItem>
                                ))}
                            </TextField>
                            <TextField label="Account Number" value={numberForm.account_number} onChange={(event) => setNumberForm((prev) => ({ ...prev, account_number: event.target.value }))} />
                            <TextField type="number" label="Last Number" value={numberForm.last_number} onChange={(event) => setNumberForm((prev) => ({ ...prev, last_number: Number(event.target.value) }))} />
                            <TextField type="number" label="Allocation Size" value={numberForm.allocation_size} onChange={(event) => setNumberForm((prev) => ({ ...prev, allocation_size: Number(event.target.value) }))} />
                            <TextField label="Reset Policy" value={numberForm.reset_policy} onChange={(event) => setNumberForm((prev) => ({ ...prev, reset_policy: event.target.value }))} />
                            <Button
                                variant="contained"
                                onClick={async () => {
                                    await fetchUpsertNumber(numberForm);
                                    setNumberForm({ recid: null, accounts_guid: "", prefix: "", account_number: "", last_number: 1000, allocation_size: 10, reset_policy: "Never" });
                                    await loadShared();
                                }}
                            >
                                Save
                            </Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Prefix</TableCell>
                                <TableCell>Account Number</TableCell>
                                <TableCell>Last Number</TableCell>
                                <TableCell>Allocation Size</TableCell>
                                <TableCell>Reset Policy</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {numbers.map((item) => (
                                <TableRow key={item.recid || `${item.accounts_guid}-${item.account_number}`}>
                                    <TableCell>{item.prefix || ""}</TableCell>
                                    <TableCell>{item.account_number}</TableCell>
                                    <TableCell>{item.last_number}</TableCell>
                                    <TableCell>{item.allocation_size}</TableCell>
                                    <TableCell>{item.reset_policy}</TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={1}>
                                            <Button size="small" onClick={() => setNumberForm(item)}>Edit</Button>
                                            <Button size="small" onClick={async () => { if (!item.recid) return; await fetchNextNumber({ recid: item.recid }); await loadShared(); }}>Get Next</Button>
                                            <Button size="small" color="error" onClick={async () => { if (!item.recid) return; await fetchDeleteNumber({ recid: item.recid }); await loadShared(); }}>Delete</Button>
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            <Dialog open={journalDialogOpen} onClose={() => setJournalDialogOpen(false)} fullWidth maxWidth="md">
                <DialogTitle>{selectedJournal?.journal_name || "Journal"}</DialogTitle>
                <DialogContent>
                    {selectedJournal && (
                        <Stack spacing={2} sx={{ mt: 1 }}>
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                                <Chip label={JOURNAL_STATUS_CONFIG[selectedJournal.journal_status]?.label || selectedJournal.journal_status} color={JOURNAL_STATUS_CONFIG[selectedJournal.journal_status]?.color || "warning"} />
                                <Typography variant="body2">Posting Key: {selectedJournal.posting_key || "-"}</Typography>
                                <Typography variant="body2">Posted By: {selectedJournal.posted_by || "-"}</Typography>
                            </Stack>
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
                                    {journalLines.map((line) => (
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
                        </Stack>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setJournalDialogOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={createJournalOpen} onClose={() => setCreateJournalOpen(false)} fullWidth maxWidth="md">
                <DialogTitle>Create Journal</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField label="Name" value={journalForm.name} onChange={(event) => setJournalForm((prev) => ({ ...prev, name: event.target.value }))} />
                            <TextField label="Description" value={journalForm.description || ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, description: event.target.value }))} />
                            <TextField label="Posting Key" value={journalForm.posting_key || ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, posting_key: event.target.value || null }))} />
                            <TextField label="Source Type" value={journalForm.source_type || ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, source_type: event.target.value || null }))} />
                            <TextField select label="Period" value={journalForm.periods_guid || ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, periods_guid: event.target.value || null }))} sx={{ minWidth: 220 }}>
                                <MenuItem value="">None</MenuItem>
                                {periods.map((period) => (
                                    <MenuItem key={period.guid} value={period.guid}>FY{period.year} - {period.period_name}</MenuItem>
                                ))}
                            </TextField>
                            <TextField select label="Ledger" value={journalForm.ledgers_recid ?? ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, ledgers_recid: event.target.value === "" ? null : Number(event.target.value) }))} sx={{ minWidth: 220 }}>
                                <MenuItem value="">None</MenuItem>
                                {ledgers.map((ledger) => (
                                    <MenuItem key={ledger.recid} value={ledger.recid}>{ledger.element_name}</MenuItem>
                                ))}
                            </TextField>
                        </Stack>
                        {journalForm.lines.map((line, index) => (
                            <Paper key={index} variant="outlined" sx={{ p: 2 }}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField label="Line" type="number" value={line.line_number} onChange={(event) => setJournalForm((prev) => ({ ...prev, lines: prev.lines.map((current, currentIndex) => currentIndex === index ? { ...current, line_number: Number(event.target.value) } : current) }))} sx={{ width: 100 }} />
                                    <TextField select label="Account" value={line.accounts_guid} onChange={(event) => setJournalForm((prev) => ({ ...prev, lines: prev.lines.map((current, currentIndex) => currentIndex === index ? { ...current, accounts_guid: event.target.value } : current) }))} sx={{ minWidth: 280 }}>
                                        <MenuItem value="">Select account</MenuItem>
                                        {postingAccounts.map((account) => (
                                            <MenuItem key={account.guid} value={account.guid}>{account.number} — {account.name}</MenuItem>
                                        ))}
                                    </TextField>
                                    <TextField label="Debit" value={line.debit} onChange={(event) => setJournalForm((prev) => ({ ...prev, lines: prev.lines.map((current, currentIndex) => currentIndex === index ? { ...current, debit: event.target.value } : current) }))} />
                                    <TextField label="Credit" value={line.credit} onChange={(event) => setJournalForm((prev) => ({ ...prev, lines: prev.lines.map((current, currentIndex) => currentIndex === index ? { ...current, credit: event.target.value } : current) }))} />
                                    <TextField label="Description" value={line.description || ""} onChange={(event) => setJournalForm((prev) => ({ ...prev, lines: prev.lines.map((current, currentIndex) => currentIndex === index ? { ...current, description: event.target.value } : current) }))} sx={{ minWidth: 240 }} />
                                    <Button color="error" onClick={() => setJournalForm((prev) => ({ ...prev, lines: prev.lines.filter((_, currentIndex) => currentIndex !== index).map((current, currentIndex) => ({ ...current, line_number: currentIndex + 1 })) }))} disabled={journalForm.lines.length === 1}>Remove</Button>
                                </Stack>
                            </Paper>
                        ))}
                        <Button onClick={() => setJournalForm((prev) => ({ ...prev, lines: [...prev.lines, DEFAULT_JOURNAL_LINE(prev.lines.length + 1)] }))}>Add Line</Button>
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCreateJournalOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={async () => {
                        await fetchJournalCreate(journalForm as any);
                        setCreateJournalOpen(false);
                        setJournalForm({
                            name: "",
                            description: null,
                            posting_key: null,
                            source_type: "manual",
                            source_id: null,
                            periods_guid: null,
                            ledgers_recid: null,
                            lines: [DEFAULT_JOURNAL_LINE(1)],
                        });
                        await loadJournals();
                    }}>Save</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={lotDialogOpen} onClose={() => setLotDialogOpen(false)} fullWidth maxWidth="md">
                <DialogTitle>Credit Lot Events</DialogTitle>
                <DialogContent>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Type</TableCell>
                                <TableCell>Credits</TableCell>
                                <TableCell>Unit Price</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Actor</TableCell>
                                <TableCell>Journal</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {lotEvents.map((event) => (
                                <TableRow key={event.recid}>
                                    <TableCell>{event.event_type}</TableCell>
                                    <TableCell>{event.credits}</TableCell>
                                    <TableCell>{event.unit_price}</TableCell>
                                    <TableCell>{event.description || "-"}</TableCell>
                                    <TableCell>{event.actor_guid || "-"}</TableCell>
                                    <TableCell>{event.journals_recid || "-"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setLotDialogOpen(false)}>Close</Button>
                </DialogActions>
            </Dialog>

            <Dialog open={grantDialogOpen} onClose={() => setGrantDialogOpen(false)} fullWidth maxWidth="sm">
                <DialogTitle>Grant Credits</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField label="User GUID" value={grantForm.users_guid} onChange={(event) => setGrantForm((prev) => ({ ...prev, users_guid: event.target.value }))} />
                        <TextField label="Credits" type="number" value={grantForm.credits} onChange={(event) => setGrantForm((prev) => ({ ...prev, credits: Number(event.target.value) }))} />
                        <TextField label="Total Paid" value={grantForm.total_paid} onChange={(event) => setGrantForm((prev) => ({ ...prev, total_paid: event.target.value }))} />
                        <TextField label="Currency" value={grantForm.currency} onChange={(event) => setGrantForm((prev) => ({ ...prev, currency: event.target.value }))} />
                        <TextField label="Expires At" value={grantForm.expires_at || ""} onChange={(event) => setGrantForm((prev) => ({ ...prev, expires_at: event.target.value || null }))} />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setGrantDialogOpen(false)}>Cancel</Button>
                    <Button variant="contained" onClick={async () => {
                        await fetchCreditLotCreate(grantForm as any);
                        setGrantDialogOpen(false);
                        await loadLots();
                    }}>Save</Button>
                </DialogActions>
            </Dialog>

            <Notification open={notification} handleClose={() => setNotification(false)} severity={notificationSeverity} message={notificationMessage} />
        </Box>
    );
};

export default FinanceAccountantPage;
