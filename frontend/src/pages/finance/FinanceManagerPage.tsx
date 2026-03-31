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
import { fetchListImports, fetchListLineItems, fetchApprove as fetchStagingApprove, fetchReject as fetchStagingReject } from '../../rpc/finance/staging';
import { fetchPeriodStatus, fetchJournalSummary, fetchTrialBalance } from '../../rpc/finance/reporting';
import { fetchList as fetchPeriodsList, fetchClose as fetchPeriodClose, fetchReopen as fetchPeriodReopen, fetchListCloseBlockers } from '../../rpc/finance/periods';
import { fetchList as fetchJournalsList, fetchLines as fetchJournalLines, fetchApprove as fetchJournalApprove, fetchReject as fetchJournalReject } from '../../rpc/finance/journals';
import { fetchList as fetchProductJournalConfigList, fetchUpsert as fetchProductJournalConfigUpsert, fetchApprove as fetchPjcApprove, fetchClose as fetchPjcClose } from '../../rpc/finance/product_journal_config';
import { fetchList as fetchProductsList } from '../../rpc/finance/products';

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
    closed_by: string | null;
    closed_on: string | null;
    locked_by: string | null;
    locked_on: string | null;
    total_journals: number;
    draft_journals: number;
    pending_approval_journals: number;
    posted_journals: number;
    reversed_journals: number;
};

type PeriodCloseBlocker = {
    period_guid: string;
    blocker_type: string;
    blocker_recid: number;
    blocker_name: string;
    blocker_reason: string;
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

type FinancePeriodItem = {
    guid: string;
    year: number;
    period_name: string;
    status: number;
};

type FinanceJournalItem = {
    recid: number;
    name: string;
    description: string | null;
    status: number;
    periods_guid: string | null;
};

type ProductJournalConfig = {
    recid: number;
    element_category: string;
    element_journal_scope: string;
    journals_recid: number;
    periods_guid: string;
    element_approved_by: string | null;
    element_approved_on: string | null;
    element_activated_by: string | null;
    element_activated_on: string | null;
    element_status: number;
    element_created_on: string | null;
    element_modified_on: string | null;
};

type Product = {
    recid: number;
    element_sku: string;
    element_name: string;
    element_description: string | null;
    element_category: string;
    element_price: string;
    element_currency: string;
    element_credits: number;
    element_enablement_key: string | null;
    element_is_recurring: boolean;
    element_sort_order: number;
    element_status: number;
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

const PRODUCT_CATEGORY_LABELS: Record<string, string> = {
    credit_purchase: "Credit Purchases",
    enablement: "Enablement",
};

const PRODUCT_JOURNAL_CONFIG_STATUS: Record<number, { label: string; color: "default" | "info" | "success" }> = {
    0: { label: "Draft", color: "default" },
    1: { label: "Approved", color: "info" },
    2: { label: "Active", color: "success" },
    3: { label: "Closed", color: "default" },
};



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

const formatDateTime = (value: string | null | undefined): string => {
    if (!value) {
        return "-";
    }
    return new Date(value).toLocaleString();
};

const normalizeProductJournalConfig = (config: {
    recid: number;
    category: string;
    journal_scope: string;
    journals_recid: number;
    periods_guid: string;
    approved_by: string | null;
    approved_on: string | null;
    activated_by: string | null;
    activated_on: string | null;
    status: number;
    created_on: string | null;
    modified_on: string | null;
}): ProductJournalConfig => ({
    recid: config.recid,
    element_category: config.category,
    element_journal_scope: config.journal_scope,
    journals_recid: config.journals_recid,
    periods_guid: config.periods_guid,
    element_approved_by: config.approved_by,
    element_approved_on: config.approved_on,
    element_activated_by: config.activated_by,
    element_activated_on: config.activated_on,
    element_status: config.status,
    element_created_on: config.created_on,
    element_modified_on: config.modified_on,
});

const normalizeProduct = (product: {
    recid: number;
    sku: string;
    name: string;
    description: string | null;
    category: string;
    price: string;
    currency: string;
    credits: number;
    enablement_key: string | null;
    is_recurring: boolean;
    sort_order: number;
    status: number;
}): Product => ({
    recid: product.recid,
    element_sku: product.sku,
    element_name: product.name,
    element_description: product.description,
    element_category: product.category,
    element_price: product.price,
    element_currency: product.currency,
    element_credits: product.credits,
    element_enablement_key: product.enablement_key,
    element_is_recurring: product.is_recurring,
    element_sort_order: product.sort_order,
    element_status: product.status,
});

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
    const [reviewPeriodGuid, setReviewPeriodGuid] = useState<string>("");
    const [reviewBlockers, setReviewBlockers] = useState<PeriodCloseBlocker[]>([]);
    const [reviewLoading, setReviewLoading] = useState(false);
    const [reviewError, setReviewError] = useState<string | null>(null);

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

    const [productJournalConfigs, setProductJournalConfigs] = useState<ProductJournalConfig[]>([]);
    const [configPeriods, setConfigPeriods] = useState<FinancePeriodItem[]>([]);
    const [draftJournals, setDraftJournals] = useState<FinanceJournalItem[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [configForm, setConfigForm] = useState({
        category: "credit_purchase",
        journal_scope: "credit_purchase",
        journals_recid: "",
        periods_guid: "",
    });
    const [configError, setConfigError] = useState<string | null>(null);
    const [configSuccess, setConfigSuccess] = useState<string | null>(null);

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

    const openPeriods = useMemo(
        () => periodStatusRows.filter((row) => row.period_status === 1),
        [periodStatusRows],
    );

    const closedPeriods = useMemo(
        () => periodStatusRows.filter((row) => row.period_status === 2),
        [periodStatusRows],
    );

    const selectedReviewPeriod = useMemo(
        () => openPeriods.find((row) => row.period_guid === reviewPeriodGuid) ?? null,
        [openPeriods, reviewPeriodGuid],
    );

    const productCategoryOptions = useMemo(() => {
        const categories = new Set<string>(Object.keys(PRODUCT_CATEGORY_LABELS));
        products.forEach((product) => {
            if (product.element_category) {
                categories.add(product.element_category);
            }
        });
        return Array.from(categories).sort((left, right) => left.localeCompare(right));
    }, [products]);

    const availableDraftJournals = useMemo(
        () => draftJournals.filter((journal) => !configForm.periods_guid || journal.periods_guid === configForm.periods_guid),
        [configForm.periods_guid, draftJournals],
    );

    const configJournalByRecid = useMemo(
        () => new Map(draftJournals.map((journal) => [journal.recid, journal])),
        [draftJournals],
    );

    const configPeriodByGuid = useMemo(
        () => new Map(configPeriods.filter((period) => Boolean(period.guid)).map((period) => [period.guid as string, period])),
        [configPeriods],
    );

    const loadApprovalQueue = useCallback(async (): Promise<void> => {
        const res = await fetchListImports({ status: 4 }) as any;
        setApprovalQueue(res.imports || []);
    }, []);

    const loadImportLineItems = useCallback(async (importsRecid: number): Promise<void> => {
        const res = await fetchListLineItems({
            imports_recid: importsRecid,
        }) as any;
        setApprovalLineItems(res.line_items || []);
    }, []);

    const loadAllPeriodStatus = useCallback(async (): Promise<void> => {
        const res = await fetchPeriodStatus({} as any) as any;
        setAllPeriodStatusRows(res.periods || []);
    }, []);

    const loadPeriodStatus = useCallback(async (): Promise<void> => {
        const res = await fetchPeriodStatus({
            fiscal_year: periodYear || null,
        }) as any;
        setPeriodStatusRows(res.periods || []);
    }, [periodYear]);

    const loadTrialBalance = useCallback(async (): Promise<void> => {
        const res = await fetchTrialBalance({
            fiscal_year: trialYear || null,
            period_guid: trialPeriodGuid || null,
        }) as any;
        setTrialRows(res.rows || []);
    }, [trialPeriodGuid, trialYear]);

    const loadJournalSummary = useCallback(async (): Promise<void> => {
        const res = await fetchJournalSummary({
            journal_status: journalStatus === "" ? null : Number(journalStatus),
            fiscal_year: journalYear || null,
            periods_guid: journalPeriodGuid || null,
        }) as any;
        setJournalRows(res.journals || []);
    }, [journalPeriodGuid, journalStatus, journalYear]);

    const loadProductJournalConfigData = useCallback(async (): Promise<void> => {
        const [configResponse, periodResponse, journalResponse, productResponse] = await Promise.all([
            fetchProductJournalConfigList({} as any) as any,
            fetchPeriodsList() as any,
            fetchJournalsList({ status: 0 } as any) as any,
            fetchProductsList({} as any) as any,
        ]);
        const openConfigPeriods = (periodResponse.periods || []).filter((period: any) => period.status === 1 && period.guid);
        const configRows = (configResponse.configs || []).map(normalizeProductJournalConfig);
        const draftJournalRows = journalResponse.journals || [];
        const productRows = (productResponse.products || []).map(normalizeProduct);
        const availableCategories: string[] = Array.from(new Set(productRows.map((product: Product) => product.element_category).filter(Boolean)));
        const defaultPeriodGuid: string = openConfigPeriods[0]?.guid || "";
        const defaultJournal = draftJournalRows.find((journal: any) => journal.periods_guid === defaultPeriodGuid) || draftJournalRows[0];
        setProductJournalConfigs(configRows);
        setConfigPeriods(openConfigPeriods);
        setDraftJournals(draftJournalRows);
        setProducts(productRows);
        setConfigForm((current) => ({
            ...current,
            periods_guid: current.periods_guid || defaultPeriodGuid,
            journals_recid: current.journals_recid || (defaultJournal ? String(defaultJournal.recid) : ""),
            category: availableCategories.includes(current.category) ? current.category : (availableCategories[0] || current.category) as string,
            journal_scope: availableCategories.includes(current.category) ? current.journal_scope : (availableCategories[0] || current.journal_scope) as string,
        }));
        setConfigError(null);
    }, []);

    const loadPendingJournals = useCallback(async (): Promise<void> => {
        const res = await fetchJournalSummary({
            journal_status: 1,
            fiscal_year: null,
            periods_guid: null,
        }) as any;
        setPendingJournals(res.journals || []);
    }, []);

    const loadPendingJournalLines = useCallback(async (recid: number): Promise<void> => {
        const res = await fetchJournalLines({ journals_recid: recid }) as any;
        setPendingJournalLines(res.lines || []);
    }, []);

    const reviewPeriodClose = useCallback(async (guid: string): Promise<void> => {
        setReviewPeriodGuid(guid);
        setReviewLoading(true);
        setReviewError(null);
        try {
            const res = await fetchListCloseBlockers({ guid }) as any;
            setReviewBlockers(res.blockers || []);
        } catch (error: unknown) {
            setReviewBlockers([]);
            setReviewError(getErrorMessage(error));
        } finally {
            setReviewLoading(false);
        }
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
        if (tab === 5) {
            void loadProductJournalConfigData();
        }
    }, [tab, loadApprovalQueue, loadJournalSummary, loadPendingJournals, loadPeriodStatus, loadProductJournalConfigData, loadTrialBalance]);

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
                <Tab label="Product Journal Config" />
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
                                                        await fetchStagingApprove({ imports_recid: row.recid });
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
                                                        await fetchJournalApprove({ recid: row.recid });
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

                    <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle1" sx={{ mb: 1 }}>Open Periods Pending Close Approval</Typography>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Period</TableCell>
                                    <TableCell>Start</TableCell>
                                    <TableCell>End</TableCell>
                                    <TableCell>Draft</TableCell>
                                    <TableCell>Pending</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {openPeriods.map((row) => (
                                    <TableRow key={row.period_guid} selected={reviewPeriodGuid === row.period_guid}>
                                        <TableCell>{row.period_name}</TableCell>
                                        <TableCell>{row.start_date}</TableCell>
                                        <TableCell>{row.end_date}</TableCell>
                                        <TableCell>{row.draft_journals}</TableCell>
                                        <TableCell>{row.pending_approval_journals}</TableCell>
                                        <TableCell>
                                            <Button size="small" variant="outlined" onClick={() => void reviewPeriodClose(row.period_guid)}>
                                                Review & Close
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {openPeriods.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={6}>No open periods are awaiting close review.</TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </Paper>

                    {selectedReviewPeriod && (
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Typography variant="subtitle1">Close Review — {selectedReviewPeriod.period_name}</Typography>
                                {reviewLoading && <Typography variant="body2">Loading close blockers…</Typography>}
                                {reviewError && <Typography color="error">{reviewError}</Typography>}
                                {!reviewLoading && !reviewError && reviewBlockers.length === 0 && (
                                    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                        <Chip color="success" label="Ready for close" />
                                        <Button
                                            variant="contained"
                                            onClick={async () => {
                                                try {
                                                    await fetchPeriodClose({ guid: selectedReviewPeriod.period_guid });
                                                    setReviewBlockers([]);
                                                    await Promise.all([loadAllPeriodStatus(), loadPeriodStatus()]);
                                                } catch (error: unknown) {
                                                    setReviewError(getErrorMessage(error));
                                                }
                                            }}
                                        >
                                            Approve Close
                                        </Button>
                                    </Stack>
                                )}
                                {!reviewLoading && reviewBlockers.length > 0 && (
                                    <Table size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Type</TableCell>
                                                <TableCell>Name</TableCell>
                                                <TableCell>Reason</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {reviewBlockers.map((blocker) => (
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

                    <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle1" sx={{ mb: 1 }}>Closed Periods</Typography>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Period</TableCell>
                                    <TableCell>Closed By</TableCell>
                                    <TableCell>Closed On</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {closedPeriods.map((row) => (
                                    <TableRow key={row.period_guid}>
                                        <TableCell>{row.period_name}</TableCell>
                                        <TableCell>{row.closed_by || "-"}</TableCell>
                                        <TableCell>{formatDateTime(row.closed_on)}</TableCell>
                                        <TableCell>
                                            <Button
                                                size="small"
                                                color="error"
                                                onClick={async () => {
                                                    try {
                                                        await fetchPeriodReopen({ guid: row.period_guid });
                                                        if (reviewPeriodGuid === row.period_guid) {
                                                            setReviewPeriodGuid("");
                                                            setReviewBlockers([]);
                                                        }
                                                        await Promise.all([loadAllPeriodStatus(), loadPeriodStatus()]);
                                                    } catch (error: unknown) {
                                                        setReviewError(getErrorMessage(error));
                                                    }
                                                }}
                                            >
                                                Reopen
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {closedPeriods.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={4}>No closed periods for the selected fiscal year.</TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </Paper>
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

            {tab === 5 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                                <Box>
                                    <Typography variant="subtitle1">Product Journal Configuration</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Assign draft or open journals to product categories for a fiscal period, then approve them for activation.
                                    </Typography>
                                </Box>
                                <Button variant="outlined" onClick={() => void loadProductJournalConfigData()}>Refresh</Button>
                            </Stack>
                            {configError && <Typography color="error">{configError}</Typography>}
                            {configSuccess && <Typography color="success.main">{configSuccess}</Typography>}
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} flexWrap="wrap">
                                <TextField
                                    select
                                    label="Category"
                                    value={configForm.category}
                                    onChange={(event) => {
                                        const nextCategory = event.target.value;
                                        setConfigForm((current) => ({
                                            ...current,
                                            category: nextCategory,
                                            journal_scope: nextCategory,
                                        }));
                                    }}
                                    sx={{ minWidth: 220 }}
                                >
                                    {productCategoryOptions.map((category) => (
                                        <MenuItem key={category} value={category}>
                                            {PRODUCT_CATEGORY_LABELS[category] || category}
                                        </MenuItem>
                                    ))}
                                </TextField>
                                <TextField
                                    label="Journal Scope"
                                    value={configForm.journal_scope}
                                    onChange={(event) => setConfigForm((current) => ({ ...current, journal_scope: event.target.value }))}
                                    sx={{ minWidth: 220 }}
                                />
                                <TextField
                                    select
                                    label="Period"
                                    value={configForm.periods_guid}
                                    onChange={(event) => {
                                        const nextPeriodGuid = event.target.value;
                                        const firstJournalForPeriod = draftJournals.find((journal) => journal.periods_guid === nextPeriodGuid);
                                        setConfigForm((current) => ({
                                            ...current,
                                            periods_guid: nextPeriodGuid,
                                            journals_recid: firstJournalForPeriod ? String(firstJournalForPeriod.recid) : "",
                                        }));
                                    }}
                                    sx={{ minWidth: 220 }}
                                >
                                    {configPeriods.map((period) => (
                                        <MenuItem key={period.guid} value={period.guid}>
                                            FY{period.year} - {period.period_name}
                                        </MenuItem>
                                    ))}
                                </TextField>
                                <TextField
                                    select
                                    label="Journal"
                                    value={configForm.journals_recid}
                                    onChange={(event) => setConfigForm((current) => ({ ...current, journals_recid: event.target.value }))}
                                    sx={{ minWidth: 260 }}
                                >
                                    {availableDraftJournals.map((journal) => (
                                        <MenuItem key={journal.recid} value={String(journal.recid)}>
                                            {journal.name} — {journal.description || "No description"}
                                        </MenuItem>
                                    ))}
                                </TextField>
                                <Button
                                    variant="contained"
                                    disabled={!configForm.category || !configForm.journal_scope.trim() || !configForm.periods_guid || !configForm.journals_recid}
                                    onClick={async () => {
                                        try {
                                            setConfigError(null);
                                            setConfigSuccess(null);
                                            await fetchProductJournalConfigUpsert({
                                                recid: null,
                                                category: configForm.category,
                                                journal_scope: configForm.journal_scope,
                                                journals_recid: Number(configForm.journals_recid),
                                                periods_guid: configForm.periods_guid,
                                                status: 0,
                                            } as any);
                                            setConfigSuccess("Product journal configuration created.");
                                            await loadProductJournalConfigData();
                                        } catch (error: unknown) {
                                            setConfigError(getErrorMessage(error));
                                        }
                                    }}
                                >
                                    Create
                                </Button>
                            </Stack>
                        </Stack>
                    </Paper>

                    <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle1" sx={{ mb: 1 }}>Existing Configurations</Typography>
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Category</TableCell>
                                    <TableCell>Journal Scope</TableCell>
                                    <TableCell>Journal</TableCell>
                                    <TableCell>Period</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Approved By</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {productJournalConfigs.map((config) => (
                                    <TableRow key={config.recid}>
                                        <TableCell>{PRODUCT_CATEGORY_LABELS[config.element_category] || config.element_category}</TableCell>
                                        <TableCell>{config.element_journal_scope}</TableCell>
                                        <TableCell>
                                            {configJournalByRecid.get(config.journals_recid)?.name || `Journal #${config.journals_recid}`}
                                        </TableCell>
                                        <TableCell>
                                            {configPeriodByGuid.get(config.periods_guid)
                                                ? `FY${configPeriodByGuid.get(config.periods_guid)?.year} — ${configPeriodByGuid.get(config.periods_guid)?.period_name}`
                                                : config.periods_guid}
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={PRODUCT_JOURNAL_CONFIG_STATUS[config.element_status]?.label || `Status ${config.element_status}`}
                                                color={PRODUCT_JOURNAL_CONFIG_STATUS[config.element_status]?.color || "default"}
                                            />
                                        </TableCell>
                                        <TableCell>{config.element_approved_by || "-"}</TableCell>
                                        <TableCell>
                                            <Stack direction="row" spacing={1}>
                                                {config.element_status === 0 && (
                                                    <Button
                                                        size="small"
                                                        variant="outlined"
                                                        onClick={async () => {
                                                            try {
                                                                setConfigError(null);
                                                                setConfigSuccess(null);
                                                                await fetchPjcApprove({ recid: config.recid });
                                                                setConfigSuccess(`Approved configuration ${config.recid}.`);
                                                                await loadProductJournalConfigData();
                                                            } catch (error: unknown) {
                                                                setConfigError(getErrorMessage(error));
                                                            }
                                                        }}
                                                    >
                                                        Approve
                                                    </Button>
                                                )}
                                                {config.element_status === 2 && (
                                                    <Button
                                                        size="small"
                                                        color="warning"
                                                        variant="outlined"
                                                        onClick={async () => {
                                                            try {
                                                                setConfigError(null);
                                                                setConfigSuccess(null);
                                                                await fetchPjcClose({ recid: config.recid });
                                                                setConfigSuccess(`Closed configuration ${config.recid}.`);
                                                                await loadProductJournalConfigData();
                                                            } catch (error: unknown) {
                                                                setConfigError(getErrorMessage(error));
                                                            }
                                                        }}
                                                    >
                                                        Close
                                                    </Button>
                                                )}
                                                {config.element_status !== 0 && config.element_status !== 2 && (
                                                    <Typography variant="body2" color="text.secondary">No action</Typography>
                                                )}
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {productJournalConfigs.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={7}>No product journal configurations created yet.</TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </Paper>
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
                            await fetchStagingReject({
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
                            await fetchJournalReject({
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
