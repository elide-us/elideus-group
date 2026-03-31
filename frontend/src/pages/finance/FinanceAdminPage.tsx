import { useCallback, useEffect, useMemo, useState } from "react";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Alert,
    Box,
    Button,
    Chip,
    Collapse,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    FormControlLabel,
    InputLabel,
    IconButton,
    MenuItem,
    Paper,
    Select,
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
    Checkbox,
} from "@mui/material";
import PageTitle from "../../components/PageTitle";
import {
    fetchDelete as fetchDeleteAccount,
    fetchList as fetchAccounts,
    fetchUpsert as fetchUpsertAccount,
} from "../../rpc/finance/accounts/index";
import {
    fetchDelete as fetchDeleteDimension,
    fetchList as fetchDimensions,
    fetchUpsert as fetchUpsertDimension,
} from "../../rpc/finance/dimensions/index";
import {
    fetchCreate as fetchCreateLedger,
    fetchDelete as fetchDeleteLedger,
    fetchList as fetchLedgers,
    fetchUpdate as fetchUpdateLedger,
} from "../../rpc/finance/ledgers/index";
import {
    fetchDelete as fetchDeleteNumber,
    fetchList as fetchNumbers,
    fetchUpsert as fetchUpsertNumber,
} from "../../rpc/finance/numbers/index";
import {
    fetchGenerateCalendar,
    fetchList as fetchPeriods,
    fetchLock as fetchPeriodLock,
    fetchUnlock as fetchPeriodUnlock,
} from "../../rpc/finance/periods/index";
import { fetchList as fetchFinanceProducts, fetchUpsert as fetchUpsertProduct, fetchDelete as fetchDeleteProduct } from "../../rpc/finance/products/index";
import { fetchList as fetchProductJournalConfigs, fetchActivate as fetchPjcActivate } from "../../rpc/finance/product_journal_config/index";
import { fetchPeriodStatus } from "../../rpc/finance/reporting/index";
import { fetchList as fetchStagingAccountMaps, fetchUpsert as fetchUpsertStagingAccountMap, fetchDelete as fetchDeleteStagingAccountMap } from "../../rpc/finance/staging_account_map/index";
import { fetchList as fetchJournalsList } from "../../rpc/finance/journals/index";
import {
    fetchDelete as fetchDeleteVendor,
    fetchList as fetchVendors,
    fetchUpsert as fetchUpsertVendor,
} from "../../rpc/finance/vendors/index";

type FinanceLedger = {
    recid: number;
    element_name: string;
    element_description: string | null;
    element_chart_of_accounts_guid: string | null;
    element_status: number;
    element_created_on: string | null;
    element_modified_on: string | null;
};

type LedgerFormState = {
    recid: number | null;
    element_name: string;
    element_description: string;
    element_chart_of_accounts_guid: string;
    element_status: number;
};

type FinancePeriod = {
    guid?: string | null;
    year: number;
    period_number: number;
    period_name: string;
    start_date: string;
    end_date: string;
    days_in_period: number;
    quarter_number: number;
    has_closing_week: boolean;
    is_leap_adjustment: boolean;
    anchor_event: string | null;
    close_type: number;
    status: number;
    numbers_recid: number | null;
    element_display_format: string | null;
    closed_by?: string | null;
    closed_on?: string | null;
    locked_by?: string | null;
    locked_on?: string | null;
};

type PeriodStatusRow = {
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

type FinanceAccount = {
    guid?: string | null;
    number: string;
    name: string;
    account_type: number;
    parent?: string | null;
    is_posting: boolean;
    status: number;
};

type FinanceDimension = {
    recid?: number | null;
    name: string;
    value: string;
    description?: string | null;
    status: number;
};

type FinanceVendor = {
    recid: number | null;
    element_name: string;
    element_display: string | null;
    element_description: string | null;
    element_status: number;
};

type FinanceNumber = {
    recid?: number | null;
    accounts_guid: string;
    prefix?: string | null;
    account_number: string;
    last_number: number;
    max_number: number | null;
    allocation_size: number;
    reset_policy: string;
    sequence_status: number;
    sequence_type: string;
    series_number: number;
    scope: string | null;
    pattern: string | null;
    display_format: string | null;
    account_name?: string | null;
    remaining?: number | null;
};

type NumberFormState = {
    recid: number | null;
    accounts_guid: string;
    prefix: string;
    account_number: string;
    last_number: number;
    max_number: number;
    allocation_size: number;
    reset_policy: string;
    sequence_status: number;
    sequence_type: string;
    series_number: number;
    scope: string;
    pattern: string;
    display_format: string;
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

type ProductFormState = {
    recid: number | null;
    element_sku: string;
    element_name: string;
    element_description: string;
    element_category: string;
    element_price: string;
    element_currency: string;
    element_credits: number;
    element_enablement_key: string;
    element_is_recurring: boolean;
    element_sort_order: number;
    element_status: number;
};

type FinanceJournalReference = {
    recid: number;
    name: string;
    description: string | null;
};

type FinancePeriodReference = {
    guid: string;
    year: number;
    period_name: string;
};

type PeriodSummary = {
    open: number;
    closed: number;
    locked: number;
};

type FinanceStagingAccountMapItem = {
    recid?: number | null;
    vendors_recid?: number | null;
    vendor_name?: string | null;
    element_service_pattern: string;
    element_meter_pattern: string | null;
    accounts_guid: string;
    account_number?: string | null;
    account_name?: string | null;
    element_priority: number;
    element_description?: string | null;
    element_status: number;
};

type MappingFormState = {
    recid: number | null;
    vendors_recid: number | null;
    element_service_pattern: string;
    element_meter_pattern: string;
    accounts_guid: string;
    element_priority: number;
    element_description: string;
    element_status: boolean;
};

const EMPTY_MAPPING_FORM: MappingFormState = {
    recid: null,
    vendors_recid: null,
    element_service_pattern: "",
    element_meter_pattern: "",
    accounts_guid: "",
    element_priority: 0,
    element_description: "",
    element_status: true,
};

const EMPTY_NUMBER_FORM: NumberFormState = {
    recid: null,
    accounts_guid: "",
    prefix: "",
    account_number: "",
    last_number: 0,
    max_number: 99999999,
    allocation_size: 1,
    reset_policy: "Never",
    sequence_status: 1,
    sequence_type: "continuous",
    series_number: 1,
    scope: "",
    pattern: "",
    display_format: "",
};

const ACCOUNT_TYPES: { value: number; label: string }[] = [
    { value: 0, label: "Asset" },
    { value: 1, label: "Liability" },
    { value: 2, label: "Equity" },
    { value: 3, label: "Revenue" },
    { value: 4, label: "Expense" },
];

const LEDGER_STATUS_OPTIONS = [
    { value: 1, label: "Active" },
    { value: 0, label: "Inactive" },
] as const;

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

const EMPTY_PRODUCT_FORM: ProductFormState = {
    recid: null,
    element_sku: "",
    element_name: "",
    element_description: "",
    element_category: "credit_purchase",
    element_price: "0.00",
    element_currency: "USD",
    element_credits: 0,
    element_enablement_key: "",
    element_is_recurring: false,
    element_sort_order: 0,
    element_status: 1,
};

const emptyLedgerForm: LedgerFormState = {
    recid: null,
    element_name: "",
    element_description: "",
    element_chart_of_accounts_guid: "",
    element_status: 1,
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

const formatDate = (value: string | null | undefined): string => {
    if (!value) {
        return "—";
    }
    return value.slice(0, 10);
};

const formatDateTime = (value: string | null | undefined): string => {
    if (!value) {
        return "—";
    }
    return new Date(value).toLocaleString();
};

const formatCurrency = (value: string, currency: string): string => {
    const amount = Number(value || 0);
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency || "USD",
    }).format(Number.isFinite(amount) ? amount : 0);
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

const getLedgerStatusLabel = (status: number): string => {
    return LEDGER_STATUS_OPTIONS.find((option) => option.value === status)?.label || `Status ${status}`;
};

const getSequenceTypeLabel = (value: string): string => {
    return value === "non_continuous" ? "Non-Continuous" : "Continuous";
};

const getSequenceTypeColor = (value: string): "info" | "default" => {
    return value === "non_continuous" ? "info" : "default";
};

const getStatusChipColor = (status: number): "success" | "error" | "default" => {
    if (status === 1) {
        return "success";
    }
    if (status === 2) {
        return "error";
    }
    if (status === 3) {
        return "error";
    }
    return "default";
};

const FinanceAdminPage = (): JSX.Element => {
    const [tab, setTab] = useState(0);
    const [forbidden, setForbidden] = useState(false);
    const [pageError, setPageError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [isBusy, setIsBusy] = useState(false);

    const [ledgers, setLedgers] = useState<FinanceLedger[]>([]);
    const [ledgerDialogOpen, setLedgerDialogOpen] = useState(false);
    const [ledgerForm, setLedgerForm] = useState<LedgerFormState>(emptyLedgerForm);

    const [periods, setPeriods] = useState<FinancePeriod[]>([]);
    const [periodStatuses, setPeriodStatuses] = useState<PeriodStatusRow[]>([]);
    const [fiscalYear, setFiscalYear] = useState<number>(new Date().getFullYear());

    const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
    const [newAccount, setNewAccount] = useState<FinanceAccount>({
        number: "",
        name: "",
        account_type: 0,
        parent: null,
        is_posting: true,
        status: 1,
    });

    const [dimensions, setDimensions] = useState<FinanceDimension[]>([]);
    const [dimensionForm, setDimensionForm] = useState<FinanceDimension>({
        recid: null,
        name: "",
        value: "",
        description: "",
        status: 1,
    });

    const [vendorList, setVendorList] = useState<FinanceVendor[]>([]);
    const [accountMappings, setAccountMappings] = useState<FinanceStagingAccountMapItem[]>([]);
    const [mappingVendorFilter, setMappingVendorFilter] = useState<string>("");
    const [mappingFormOpen, setMappingFormOpen] = useState(false);
    const [mappingForm, setMappingForm] = useState<MappingFormState>(EMPTY_MAPPING_FORM);
    const [numbers, setNumbers] = useState<FinanceNumber[]>([]);
    const [numberFormOpen, setNumberFormOpen] = useState(false);
    const [numberForm, setNumberForm] = useState<NumberFormState>(EMPTY_NUMBER_FORM);
    const [vendorFormOpen, setVendorFormOpen] = useState(false);
    const [vendorForm, setVendorForm] = useState({
        recid: null as number | null,
        element_name: "",
        element_display: "",
        element_description: "",
        element_status: true,
    });
    const [products, setProducts] = useState<Product[]>([]);
    const [productFormOpen, setProductFormOpen] = useState(false);
    const [productForm, setProductForm] = useState<ProductFormState>(EMPTY_PRODUCT_FORM);
    const [productToDelete, setProductToDelete] = useState<Product | null>(null);
    const [approvedProductConfigs, setApprovedProductConfigs] = useState<ProductJournalConfig[]>([]);
    const [activeProductConfigs, setActiveProductConfigs] = useState<ProductJournalConfig[]>([]);
    const [productConfigPeriods, setProductConfigPeriods] = useState<FinancePeriodReference[]>([]);
    const [productConfigJournals, setProductConfigJournals] = useState<FinanceJournalReference[]>([]);

    const loadLedgers = useCallback(async (): Promise<void> => {
        const response = await fetchLedgers();
        setLedgers((response.ledgers || []) as FinanceLedger[]);
    }, []);

    const loadPeriods = useCallback(async (): Promise<void> => {
        const response = await fetchPeriods();
        setPeriods((response.periods || []) as FinancePeriod[]);
    }, []);

    const loadPeriodStatuses = useCallback(async (): Promise<void> => {
        const response = await (fetchPeriodStatus as any)();
        setPeriodStatuses((response.periods || []) as PeriodStatusRow[]);
    }, []);

    const loadAccounts = useCallback(async (): Promise<void> => {
        const response = await fetchAccounts();
        setAccounts((response.accounts || []) as FinanceAccount[]);
    }, []);

    const loadDimensions = useCallback(async (): Promise<void> => {
        const response = await fetchDimensions();
        setDimensions((response.dimensions || []) as FinanceDimension[]);
    }, []);

    const loadVendors = useCallback(async (): Promise<void> => {
        const response = await fetchVendors();
        setVendorList((response.vendors || []) as FinanceVendor[]);
    }, []);

    const loadNumbers = useCallback(async (): Promise<void> => {
        const response = await fetchNumbers();
        setNumbers((response.numbers || []) as FinanceNumber[]);
    }, []);

    const loadProducts = useCallback(async (): Promise<void> => {
        const response = await fetchFinanceProducts({} as any) as any;
        setProducts((response.products || []).map(normalizeProduct));
    }, []);

    const loadApprovedProductConfigs = useCallback(async (): Promise<void> => {
        const response = await fetchProductJournalConfigs({ status: 1 } as any) as any;
        setApprovedProductConfigs((response.configs || []).map(normalizeProductJournalConfig));
    }, []);

    const loadActiveProductConfigs = useCallback(async (): Promise<void> => {
        const response = await fetchProductJournalConfigs({ status: 2 } as any) as any;
        setActiveProductConfigs((response.configs || []).map(normalizeProductJournalConfig));
    }, []);

    const loadProductConfigReferences = useCallback(async (): Promise<void> => {
        const [periodResponse, journalResponse] = await Promise.all([
            fetchPeriods() as any,
            fetchJournalsList({} as any) as any,
        ]);
        setProductConfigPeriods(
            (periodResponse.periods || [])
                .filter((period: any) => Boolean(period.guid))
                .map((period: any) => ({
                    guid: period.guid as string,
                    year: period.year,
                    period_name: period.period_name,
                })),
        );
        setProductConfigJournals((journalResponse.journals || []).map((journal: any) => ({
            recid: journal.recid,
            name: journal.name,
            description: journal.description,
        })));
    }, []);

    const loadAccountMappings = useCallback(async (): Promise<void> => {
        const payload = mappingVendorFilter ? { vendors_recid: Number(mappingVendorFilter) } : {};
        const response = await fetchStagingAccountMaps(payload) as any;
        setAccountMappings(response.mappings || []);
    }, [mappingVendorFilter]);

    const loadAll = useCallback(async (): Promise<void> => {
        try {
            setPageError(null);
            await Promise.all([
                loadLedgers(),
                loadPeriods(),
                loadPeriodStatuses(),
                loadAccounts(),
                loadDimensions(),
                loadNumbers(),
            ]);
            setForbidden(false);
        } catch (error: unknown) {
            const response = typeof error === "object" && error !== null ? Reflect.get(error, "response") : null;
            const status = typeof response === "object" && response !== null ? Reflect.get(response, "status") : null;
            if (status === 403) {
                setForbidden(true);
                return;
            }
            setPageError(getErrorMessage(error));
        }
    }, [loadAccounts, loadDimensions, loadLedgers, loadNumbers, loadPeriods, loadPeriodStatuses]);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    useEffect(() => {
        if (tab === 4) {
            void loadVendors();
        }
        if (tab === 5) {
            void Promise.all([loadVendors(), loadAccountMappings()]);
        }
        if (tab === 6) {
            void loadNumbers();
        }
        if (tab === 7) {
            void Promise.all([
                loadProducts(),
                loadApprovedProductConfigs(),
                loadActiveProductConfigs(),
                loadProductConfigReferences(),
            ]);
        }
    }, [loadAccountMappings, loadActiveProductConfigs, loadApprovedProductConfigs, loadNumbers, loadProductConfigReferences, loadProducts, loadVendors, tab]);

    const periodYears = useMemo(() => {
        const years = new Set<number>();
        periods.forEach((period) => years.add(period.year));
        periodStatuses.forEach((row) => years.add(row.fiscal_year));
        years.add(fiscalYear);
        return Array.from(years).sort((left, right) => right - left);
    }, [fiscalYear, periods, periodStatuses]);

    const groupedPeriods = useMemo(() => {
        return periodYears.map((year) => ({
            year,
            periods: periods
                .filter((period) => period.year === year)
                .sort((left, right) => left.period_number - right.period_number),
        }));
    }, [periodYears, periods]);

    const periodSummaryByYear = useMemo(() => {
        return periodStatuses.reduce<Record<number, PeriodSummary>>((summary, row) => {
            if (!summary[row.fiscal_year]) {
                summary[row.fiscal_year] = { open: 0, closed: 0, locked: 0 };
            }
            if (row.period_status === 1) {
                summary[row.fiscal_year].open += 1;
            } else if (row.period_status === 2) {
                summary[row.fiscal_year].closed += 1;
            } else if (row.period_status === 3) {
                summary[row.fiscal_year].locked += 1;
            }
            return summary;
        }, {});
    }, [periodStatuses]);

    const hasPeriodsForSelectedYear = useMemo(() => {
        return periods.some((period) => period.year === fiscalYear);
    }, [fiscalYear, periods]);

    const productCategoryOptions = useMemo(() => {
        const categories = new Set<string>(Object.keys(PRODUCT_CATEGORY_LABELS));
        products.forEach((product) => {
            if (product.element_category) {
                categories.add(product.element_category);
            }
        });
        return Array.from(categories).sort((left, right) => left.localeCompare(right));
    }, [products]);

    const productConfigPeriodByGuid = useMemo(
        () => new Map(productConfigPeriods.map((period) => [period.guid, period])),
        [productConfigPeriods],
    );

    const productConfigJournalByRecid = useMemo(
        () => new Map(productConfigJournals.map((journal) => [journal.recid, journal])),
        [productConfigJournals],
    );

    const closeLedgerDialog = (): void => {
        setLedgerDialogOpen(false);
        setLedgerForm(emptyLedgerForm);
    };

    const openCreateLedgerDialog = (): void => {
        setPageError(null);
        setSuccessMessage(null);
        setLedgerForm(emptyLedgerForm);
        setLedgerDialogOpen(true);
    };

    const openEditLedgerDialog = (ledger: FinanceLedger): void => {
        setPageError(null);
        setSuccessMessage(null);
        setLedgerForm({
            recid: ledger.recid,
            element_name: ledger.element_name,
            element_description: ledger.element_description || "",
            element_chart_of_accounts_guid: ledger.element_chart_of_accounts_guid || "",
            element_status: ledger.element_status,
        });
        setLedgerDialogOpen(true);
    };

    const closeProductFormDialog = (): void => {
        setProductFormOpen(false);
        setProductForm(EMPTY_PRODUCT_FORM);
    };

    const openCreateProductDialog = (): void => {
        setPageError(null);
        setSuccessMessage(null);
        setProductForm(EMPTY_PRODUCT_FORM);
        setProductFormOpen(true);
    };

    const openEditProductDialog = (product: Product): void => {
        setPageError(null);
        setSuccessMessage(null);
        setProductForm({
            recid: product.recid,
            element_sku: product.element_sku,
            element_name: product.element_name,
            element_description: product.element_description || "",
            element_category: product.element_category,
            element_price: product.element_price,
            element_currency: product.element_currency,
            element_credits: product.element_credits,
            element_enablement_key: product.element_enablement_key || "",
            element_is_recurring: product.element_is_recurring,
            element_sort_order: product.element_sort_order,
            element_status: product.element_status,
        });
        setProductFormOpen(true);
    };

    const saveProduct = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchUpsertProduct({
                recid: productForm.recid,
                sku: productForm.element_sku,
                name: productForm.element_name,
                description: productForm.element_description || null,
                category: productForm.element_category,
                price: productForm.element_price,
                currency: productForm.element_currency,
                credits: productForm.element_credits,
                enablement_key: productForm.element_enablement_key || null,
                is_recurring: productForm.element_is_recurring,
                sort_order: productForm.element_sort_order,
                status: productForm.element_status,
            });
            closeProductFormDialog();
            setSuccessMessage(productForm.recid === null ? "Product created." : "Product updated.");
            await loadProducts();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const confirmDeleteProduct = async (): Promise<void> => {
        if (!productToDelete) {
            return;
        }
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchDeleteProduct({ recid: productToDelete.recid });
            setSuccessMessage(`Deleted product ${productToDelete.element_sku}.`);
            setProductToDelete(null);
            await loadProducts();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const refreshFinanceAdminData = useCallback(async (): Promise<void> => {
        await Promise.all([loadLedgers(), loadPeriods(), loadPeriodStatuses()]);
    }, [loadLedgers, loadPeriodStatuses, loadPeriods]);

    const submitLedger = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);

            const payload = {
                element_name: ledgerForm.element_name.trim(),
                element_description: ledgerForm.element_description.trim() || null,
                element_chart_of_accounts_guid: ledgerForm.element_chart_of_accounts_guid || null,
            };

            if (ledgerForm.recid === null) {
                await fetchCreateLedger(payload);
                setSuccessMessage(`Created ledger ${payload.element_name}.`);
            } else {
                await fetchUpdateLedger({
                    recid: ledgerForm.recid,
                    ...payload,
                    element_status: ledgerForm.element_status,
                });
                setSuccessMessage(`Updated ledger ${payload.element_name}.`);
            }

            closeLedgerDialog();
            await loadLedgers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handleDeleteLedger = async (ledger: FinanceLedger): Promise<void> => {
        if (!window.confirm(`Delete ledger ${ledger.element_name}? This will mark it inactive.`)) {
            return;
        }
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchDeleteLedger({ recid: ledger.recid });
            setSuccessMessage(`Deleted ledger ${ledger.element_name}.`);
            await loadLedgers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handleGenerateCalendar = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            const response = await fetchGenerateCalendar({ fiscal_year: fiscalYear } as any);
            const createdCount = Array.isArray(response.periods) ? response.periods.length : 0;
            setSuccessMessage(`Generated ${createdCount} fiscal periods for ${fiscalYear}.`);
            await refreshFinanceAdminData();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handleLockToggle = async (period: FinancePeriod): Promise<void> => {
        if (!period.guid) {
            return;
        }
        const isLock = period.status === 2;
        const confirmationMessage = isLock
            ? `Lock period ${period.period_name}?`
            : `Unlock period ${period.period_name}?`;

        if (!window.confirm(confirmationMessage)) {
            return;
        }

        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await (isLock ? fetchPeriodLock : fetchPeriodUnlock)({
                guid: period.guid,
            });
            setSuccessMessage(`${isLock ? "Locked" : "Unlocked"} ${period.period_name}.`);
            await refreshFinanceAdminData();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const saveAccount = async (): Promise<void> => {
        try {
            setPageError(null);
            await fetchUpsertAccount(newAccount as any);
            setNewAccount({
                number: "",
                name: "",
                account_type: 0,
                parent: null,
                is_posting: true,
                status: 1,
            });
            await loadAccounts();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const saveDimension = async (): Promise<void> => {
        try {
            setPageError(null);
            await fetchUpsertDimension(dimensionForm as any);
            setDimensionForm({ recid: null, name: "", value: "", description: "", status: 1 });
            await loadDimensions();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const openMappingForm = (mapping?: FinanceStagingAccountMapItem): void => {
        if (!mapping) {
            setMappingForm(EMPTY_MAPPING_FORM);
            setMappingFormOpen(true);
            return;
        }
        setMappingForm({
            recid: typeof mapping.recid === "number" ? mapping.recid : null,
            vendors_recid: typeof mapping.vendors_recid === "number" ? mapping.vendors_recid : null,
            element_service_pattern: mapping.element_service_pattern || "",
            element_meter_pattern: String(mapping.element_meter_pattern || ""),
            accounts_guid: mapping.accounts_guid || "",
            element_priority: Number(mapping.element_priority || 0),
            element_description: String(mapping.element_description || ""),
            element_status: Number(mapping.element_status) === 1,
        });
        setMappingFormOpen(true);
    };

    const saveAccountMapping = async (): Promise<void> => {
        try {
            setPageError(null);
            setSuccessMessage(null);
            await fetchUpsertStagingAccountMap({
                recid: mappingForm.recid,
                vendors_recid: mappingForm.vendors_recid,
                element_service_pattern: mappingForm.element_service_pattern,
                element_meter_pattern: mappingForm.element_meter_pattern || null,
                accounts_guid: mappingForm.accounts_guid,
                element_priority: mappingForm.element_priority,
                element_description: mappingForm.element_description || null,
                element_status: mappingForm.element_status ? 1 : 0,
            } as any);
            setMappingForm(EMPTY_MAPPING_FORM);
            setMappingFormOpen(false);
            setSuccessMessage("Account mapping saved.");
            await loadAccountMappings();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const deleteAccountMapping = async (recid: number | null | undefined): Promise<void> => {
        if (!recid) {
            return;
        }
        try {
            setPageError(null);
            setSuccessMessage(null);
            await fetchDeleteStagingAccountMap({ recid });
            setSuccessMessage("Account mapping deleted.");
            await loadAccountMappings();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const saveVendor = async (): Promise<void> => {
        if (!vendorForm.element_name.trim()) {
            return;
        }
        try {
            setPageError(null);
            await fetchUpsertVendor({
                recid: vendorForm.recid,
                element_name: vendorForm.element_name,
                element_display: vendorForm.element_display || null,
                element_description: vendorForm.element_description || null,
                element_status: vendorForm.element_status ? 1 : 0,
            });
            setVendorFormOpen(false);
            setVendorForm({
                recid: null,
                element_name: "",
                element_display: "",
                element_description: "",
                element_status: true,
            });
            await loadVendors();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const openNumberForm = (sequence?: FinanceNumber): void => {
        setPageError(null);
        setSuccessMessage(null);
        if (!sequence) {
            setNumberForm(EMPTY_NUMBER_FORM);
            setNumberFormOpen(true);
            return;
        }
        setNumberForm({
            recid: sequence.recid ?? null,
            accounts_guid: sequence.accounts_guid || "",
            prefix: sequence.prefix || "",
            account_number: sequence.account_number || "",
            last_number: Number(sequence.last_number || 0),
            max_number: Number(sequence.max_number || 99999999),
            allocation_size: Number(sequence.allocation_size || 1),
            reset_policy: sequence.reset_policy || "Never",
            sequence_status: Number(sequence.sequence_status || 1),
            sequence_type: sequence.sequence_type || "continuous",
            series_number: Number(sequence.series_number || 1),
            scope: sequence.scope || "",
            pattern: sequence.pattern || "",
            display_format: sequence.display_format || "",
        });
        setNumberFormOpen(true);
    };

    const saveNumber = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchUpsertNumber({
                recid: numberForm.recid,
                accounts_guid: numberForm.accounts_guid,
                prefix: numberForm.prefix || null,
                account_number: numberForm.account_number,
                last_number: numberForm.last_number,
                max_number: numberForm.max_number,
                allocation_size: numberForm.allocation_size,
                reset_policy: numberForm.reset_policy,
                sequence_status: numberForm.sequence_status,
                sequence_type: numberForm.sequence_type,
                series_number: numberForm.series_number,
                scope: numberForm.scope || null,
                pattern: numberForm.pattern || null,
                display_format: numberForm.display_format || null,
            } as any);
            setNumberForm(EMPTY_NUMBER_FORM);
            setNumberFormOpen(false);
            setSuccessMessage("Number sequence saved.");
            await loadNumbers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const deleteNumber = async (sequence: FinanceNumber): Promise<void> => {
        if (!sequence.recid || !window.confirm(`Delete sequence ${sequence.account_number}?`)) {
            return;
        }
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchDeleteNumber({ recid: sequence.recid });
            setSuccessMessage(`Deleted sequence ${sequence.account_number}.`);
            await loadNumbers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Access denied</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Finance Admin</PageTitle>
            <Divider sx={{ mb: 2 }} />

            {pageError && <Alert severity="error" sx={{ mb: 2 }}>{pageError}</Alert>}
            {successMessage && <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert>}

            <Tabs value={tab} onChange={(_, next) => setTab(next)}>
                <Tab label="Ledgers" />
                <Tab label="Fiscal Calendar" />
                <Tab label="Chart of Accounts" />
                <Tab label="Financial Dimensions" />
                <Tab label="Vendors" />
                <Tab label="Account Mappings" />
                <Tab label="Number Sequences" />
                <Tab label="Product Config" />
            </Tabs>

            {tab === 0 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                            <Box>
                                <Typography variant="h6">Ledger management</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Create and manage the General Ledger and any future reporting ledgers.
                                </Typography>
                            </Box>
                            <Button startIcon={<AddIcon />} variant="contained" onClick={openCreateLedgerDialog}>
                                Create ledger
                            </Button>
                        </Stack>
                    </Paper>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Created</TableCell>
                                <TableCell align="right">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {ledgers.map((ledger) => (
                                <TableRow key={ledger.recid}>
                                    <TableCell>{ledger.element_name}</TableCell>
                                    <TableCell>{ledger.element_description || "—"}</TableCell>
                                    <TableCell>
                                        <Chip
                                            color={ledger.element_status === 1 ? "success" : "default"}
                                            label={getLedgerStatusLabel(ledger.element_status)}
                                        />
                                    </TableCell>
                                    <TableCell>{formatDateTime(ledger.element_created_on)}</TableCell>
                                    <TableCell align="right">
                                        <IconButton aria-label={`Edit ${ledger.element_name}`} onClick={() => openEditLedgerDialog(ledger)}>
                                            <EditIcon fontSize="small" />
                                        </IconButton>
                                        <IconButton
                                            aria-label={`Delete ${ledger.element_name}`}
                                            color="error"
                                            onClick={() => void handleDeleteLedger(ledger)}
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {ledgers.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6}>
                                        <Typography variant="body2" color="text.secondary">
                                            No ledgers have been created yet.
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 1 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ xs: "stretch", md: "center" }}>
                                <TextField
                                    type="number"
                                    label="Fiscal Year"
                                    value={fiscalYear}
                                    onChange={(event) => setFiscalYear(Number(event.target.value))}
                                    sx={{ maxWidth: 220 }}
                                />
                                <Button
                                    variant="contained"
                                    disabled={isBusy || !Number.isFinite(fiscalYear) || hasPeriodsForSelectedYear}
                                    onClick={() => void handleGenerateCalendar()}
                                >
                                    Generate fiscal year
                                </Button>
                                {hasPeriodsForSelectedYear && (
                                    <Alert severity="warning" sx={{ py: 0 }}>
                                        Fiscal year {fiscalYear} already has generated periods.
                                    </Alert>
                                )}
                            </Stack>
                            <Typography variant="body2" color="text.secondary">
                                The calendar generator creates 12 standard 28-day periods and 4 closing weeks using the
                                4-4-5 fiscal pattern.
                            </Typography>
                        </Stack>
                    </Paper>

                    <Stack direction={{ xs: "column", md: "row" }} spacing={2} flexWrap="wrap">
                        {periodYears.map((year) => {
                            const summary = periodSummaryByYear[year] || { open: 0, closed: 0, locked: 0 };
                            return (
                                <Paper key={year} sx={{ p: 2, minWidth: 220 }}>
                                    <Typography variant="subtitle1">FY {year}</Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                        <Chip color="success" label={`${summary.open} Open`} />
                                        <Chip color="error" label={`${summary.closed} Closed`} />
                                        <Chip color="error" label={`${summary.locked} Locked`} />
                                    </Stack>
                                </Paper>
                            );
                        })}
                    </Stack>

                    {groupedPeriods.map(({ year, periods: periodsForYear }) => (
                        <Accordion key={year} defaultExpanded={year === fiscalYear}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ md: "center" }}>
                                    <Typography variant="h6">Fiscal Year {year}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {periodsForYear.length} periods
                                    </Typography>
                                </Stack>
                            </AccordionSummary>
                            <AccordionDetails>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>#</TableCell>
                                            <TableCell>Name</TableCell>
                                            <TableCell>Start</TableCell>
                                            <TableCell>End</TableCell>
                                            <TableCell>Days</TableCell>
                                            <TableCell>Quarter</TableCell>
                                            <TableCell>Closing Week</TableCell>
                                            <TableCell>Status</TableCell>
                                            <TableCell>Actions</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {periodsForYear.map((period) => {
                                            return (
                                                <TableRow key={period.guid || `${period.year}-${period.period_number}`}>
                                                    <TableCell>{period.period_number}</TableCell>
                                                    <TableCell>
                                                        <Stack direction="row" spacing={1} alignItems="center">
                                                            <Typography variant="body2">{period.period_name}</Typography>
                                                            {period.is_leap_adjustment && (
                                                                <Chip color="info" label="53-week adj." />
                                                            )}
                                                        </Stack>
                                                    </TableCell>
                                                    <TableCell>{formatDate(period.start_date)}</TableCell>
                                                    <TableCell>{formatDate(period.end_date)}</TableCell>
                                                    <TableCell>{period.days_in_period}</TableCell>
                                                    <TableCell>{period.quarter_number}</TableCell>
                                                    <TableCell>{period.has_closing_week ? "Yes" : "No"}</TableCell>
                                                    <TableCell>
                                                        <Stack spacing={1}>
                                                            <Chip
                                                                color={getStatusChipColor(period.status)}
                                                                label={period.status === 1 ? "Open" : period.status === 2 ? "Closed" : "Locked"}
                                                            />
                                                            {period.closed_by && (
                                                                <Typography variant="caption" color="text.secondary">
                                                                    Closed by {period.closed_by} on {formatDateTime(period.closed_on)}
                                                                </Typography>
                                                            )}
                                                            {period.locked_by && (
                                                                <Typography variant="caption" color="text.secondary">
                                                                    Locked by {period.locked_by} on {formatDateTime(period.locked_on)}
                                                                </Typography>
                                                            )}
                                                        </Stack>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Stack direction={{ xs: "column", md: "row" }} spacing={1} alignItems={{ md: "center" }}>
                                                            {period.status === 2 && (
                                                                <Button size="small" variant="contained" onClick={() => void handleLockToggle(period)}>
                                                                    Lock
                                                                </Button>
                                                            )}
                                                            {period.status === 3 && (
                                                                <Button size="small" color="warning" variant="outlined" onClick={() => void handleLockToggle(period)}>
                                                                    Unlock
                                                                </Button>
                                                            )}
                                                            {period.status === 1 && <Typography variant="body2">Manager closes periods.</Typography>}
                                                        </Stack>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                        {periodsForYear.length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={9}>
                                                    <Typography variant="body2" color="text.secondary">
                                                        No periods generated for this fiscal year.
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </AccordionDetails>
                        </Accordion>
                    ))}
                </Stack>
            )}

            {tab === 2 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField
                                label="Account Number"
                                value={newAccount.number}
                                onChange={(event) => setNewAccount({ ...newAccount, number: event.target.value })}
                            />
                            <TextField
                                label="Name"
                                value={newAccount.name}
                                onChange={(event) => setNewAccount({ ...newAccount, name: event.target.value })}
                            />
                            <TextField
                                select
                                label="Type"
                                value={newAccount.account_type}
                                onChange={(event) =>
                                    setNewAccount({ ...newAccount, account_type: Number(event.target.value) })
                                }
                            >
                                {ACCOUNT_TYPES.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </TextField>
                            <Button variant="contained" onClick={() => void saveAccount()}>
                                Save
                            </Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Number</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell />
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {accounts.map((item) => (
                                <TableRow key={item.guid || item.number}>
                                    <TableCell>{item.number}</TableCell>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell>
                                        {ACCOUNT_TYPES.find((option) => option.value === item.account_type)?.label || item.account_type}
                                    </TableCell>
                                    <TableCell>{item.status}</TableCell>
                                    <TableCell>
                                        <Button onClick={() => setNewAccount(item)}>Edit</Button>
                                        <Button
                                            color="error"
                                            onClick={async () => {
                                                if (!item.guid) {
                                                    return;
                                                }
                                                await fetchDeleteAccount({ guid: item.guid });
                                                await loadAccounts();
                                            }}
                                        >
                                            Delete
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 3 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField
                                label="Dimension Name"
                                value={dimensionForm.name}
                                onChange={(event) => setDimensionForm({ ...dimensionForm, name: event.target.value })}
                            />
                            <TextField
                                label="Value"
                                value={dimensionForm.value}
                                onChange={(event) => setDimensionForm({ ...dimensionForm, value: event.target.value })}
                            />
                            <TextField
                                label="Description"
                                value={dimensionForm.description}
                                onChange={(event) =>
                                    setDimensionForm({ ...dimensionForm, description: event.target.value })
                                }
                            />
                            <Button variant="contained" onClick={() => void saveDimension()}>
                                Save
                            </Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Value</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell />
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {dimensions.map((item) => (
                                <TableRow key={item.recid || `${item.name}:${item.value}`}>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell>{item.value}</TableCell>
                                    <TableCell>{item.description || ""}</TableCell>
                                    <TableCell>{item.status}</TableCell>
                                    <TableCell>
                                        <Button onClick={() => setDimensionForm(item)}>Edit</Button>
                                        <Button
                                            color="error"
                                            onClick={async () => {
                                                if (!item.recid) {
                                                    return;
                                                }
                                                await fetchDeleteDimension({ recid: item.recid });
                                                await loadDimensions();
                                            }}
                                        >
                                            Delete
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 4 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center" flexWrap="wrap">
                            <Typography variant="subtitle1">Vendors</Typography>
                            <Button
                                variant="contained"
                                onClick={() => {
                                    setVendorForm({
                                        recid: null,
                                        element_name: "",
                                        element_display: "",
                                        element_description: "",
                                        element_status: true,
                                    });
                                    setVendorFormOpen(true);
                                }}
                            >
                                Create Vendor
                            </Button>
                        </Stack>
                    </Paper>

                    <Collapse in={vendorFormOpen}>
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField
                                        label="Name"
                                        required
                                        value={vendorForm.element_name}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_name: event.target.value }))
                                        }
                                    />
                                    <TextField
                                        label="Display Name"
                                        value={vendorForm.element_display}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_display: event.target.value }))
                                        }
                                    />
                                    <TextField
                                        label="Description"
                                        value={vendorForm.element_description}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_description: event.target.value }))
                                        }
                                    />
                                    <FormControlLabel
                                        label="Active"
                                        control={
                                            <Checkbox
                                                checked={vendorForm.element_status}
                                                onChange={(event) =>
                                                    setVendorForm((previous) => ({
                                                        ...previous,
                                                        element_status: event.target.checked,
                                                    }))
                                                }
                                            />
                                        }
                                    />
                                </Stack>
                                <Stack direction="row" spacing={1}>
                                    <Button variant="contained" onClick={() => void saveVendor()}>
                                        Save
                                    </Button>
                                    <Button
                                        onClick={() => {
                                            setVendorFormOpen(false);
                                            setVendorForm({
                                                recid: null,
                                                element_name: "",
                                                element_display: "",
                                                element_description: "",
                                                element_status: true,
                                            });
                                        }}
                                    >
                                        Cancel
                                    </Button>
                                </Stack>
                            </Stack>
                        </Paper>
                    </Collapse>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Display Name</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {vendorList.map((item) => (
                                <TableRow key={item.recid || item.element_name}>
                                    <TableCell>{item.element_name}</TableCell>
                                    <TableCell>{item.element_display || ""}</TableCell>
                                    <TableCell>{item.element_description || ""}</TableCell>
                                    <TableCell>
                                        <Chip
                                            color={item.element_status === 1 ? "success" : "default"}
                                            label={item.element_status === 1 ? "Active" : "Disabled"}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={1}>
                                            <Button
                                                size="small"
                                                onClick={() => {
                                                    setVendorForm({
                                                        recid: item.recid || null,
                                                        element_name: item.element_name || "",
                                                        element_display: item.element_display || "",
                                                        element_description: item.element_description || "",
                                                        element_status: Number(item.element_status) === 1,
                                                    });
                                                    setVendorFormOpen(true);
                                                }}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                size="small"
                                                color="error"
                                                onClick={async () => {
                                                    if (!item.recid || !window.confirm(`Delete vendor ${item.element_name}?`)) {
                                                        return;
                                                    }
                                                    await fetchDeleteVendor({ recid: item.recid });
                                                    await loadVendors();
                                                }}
                                            >
                                                Delete
                                            </Button>
                                        </Stack>
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
                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" flexWrap="wrap">
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                                <TextField
                                    select
                                    label="Vendor Filter"
                                    value={mappingVendorFilter}
                                    onChange={(event) => setMappingVendorFilter(event.target.value)}
                                    sx={{ minWidth: 220 }}
                                >
                                    <MenuItem value="">All Vendors</MenuItem>
                                    {vendorList.map((vendor) => (
                                        <MenuItem key={vendor.recid || vendor.element_name} value={vendor.recid || ""}>
                                            {vendor.element_name}
                                        </MenuItem>
                                    ))}
                                </TextField>
                                <Button variant="outlined" onClick={() => void loadAccountMappings()}>Refresh</Button>
                            </Stack>
                            <Button variant="contained" onClick={() => openMappingForm()}>Create Mapping</Button>
                        </Stack>
                    </Paper>

                    <Collapse in={mappingFormOpen}>
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField
                                        select
                                        label="Vendor"
                                        value={mappingForm.vendors_recid ?? ""}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, vendors_recid: event.target.value === "" ? null : Number(event.target.value) }))}
                                        sx={{ minWidth: 220 }}
                                    >
                                        <MenuItem value="">Any Vendor</MenuItem>
                                        {vendorList.map((vendor) => (
                                            <MenuItem key={vendor.recid || vendor.element_name} value={vendor.recid || ""}>
                                                {vendor.element_name}
                                            </MenuItem>
                                        ))}
                                    </TextField>
                                    <TextField
                                        label="Service Pattern"
                                        value={mappingForm.element_service_pattern}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, element_service_pattern: event.target.value }))}
                                    />
                                    <TextField
                                        label="Meter Pattern"
                                        value={mappingForm.element_meter_pattern}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, element_meter_pattern: event.target.value }))}
                                    />
                                    <TextField
                                        select
                                        label="Account"
                                        value={mappingForm.accounts_guid}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, accounts_guid: event.target.value }))}
                                        sx={{ minWidth: 260 }}
                                    >
                                        <MenuItem value="">Select account</MenuItem>
                                        {accounts.filter((account) => account.is_posting).map((account) => (
                                            <MenuItem key={account.guid || account.number} value={account.guid || ""}>
                                                {account.number} — {account.name}
                                            </MenuItem>
                                        ))}
                                    </TextField>
                                    <TextField
                                        label="Priority"
                                        type="number"
                                        value={mappingForm.element_priority}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, element_priority: Number(event.target.value) }))}
                                        sx={{ width: 120 }}
                                    />
                                    <TextField
                                        label="Description"
                                        value={mappingForm.element_description}
                                        onChange={(event) => setMappingForm((previous) => ({ ...previous, element_description: event.target.value }))}
                                        sx={{ minWidth: 220 }}
                                    />
                                    <FormControlLabel
                                        label="Active"
                                        control={<Checkbox checked={mappingForm.element_status} onChange={(event) => setMappingForm((previous) => ({ ...previous, element_status: event.target.checked }))} />}
                                    />
                                </Stack>
                                <Stack direction="row" spacing={1}>
                                    <Button variant="contained" onClick={() => void saveAccountMapping()}>Save</Button>
                                    <Button onClick={() => { setMappingForm(EMPTY_MAPPING_FORM); setMappingFormOpen(false); }}>Cancel</Button>
                                </Stack>
                            </Stack>
                        </Paper>
                    </Collapse>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Vendor</TableCell>
                                <TableCell>Service Pattern</TableCell>
                                <TableCell>Meter Pattern</TableCell>
                                <TableCell>Account</TableCell>
                                <TableCell>Priority</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {accountMappings.map((mapping) => (
                                <TableRow key={mapping.recid || `${mapping.accounts_guid}-${mapping.element_service_pattern}`}>
                                    <TableCell>{mapping.vendor_name || "Any Vendor"}</TableCell>
                                    <TableCell>{mapping.element_service_pattern}</TableCell>
                                    <TableCell>{mapping.element_meter_pattern || "*"}</TableCell>
                                    <TableCell>{mapping.account_number ? `${mapping.account_number} — ${mapping.account_name || mapping.accounts_guid}` : mapping.accounts_guid}</TableCell>
                                    <TableCell>{mapping.element_priority}</TableCell>
                                    <TableCell><Chip color={mapping.element_status === 1 ? "success" : "default"} label={mapping.element_status === 1 ? "Active" : "Disabled"} /></TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={1}>
                                            <Button size="small" onClick={() => openMappingForm(mapping)}>Edit</Button>
                                            <Button size="small" color="error" onClick={() => void deleteAccountMapping(mapping.recid)}>Delete</Button>
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 6 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" flexWrap="wrap">
                            <Box>
                                <Typography variant="h6">Number sequences</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Manage scoped numbering families, sequence types, and current rollover series.
                                </Typography>
                            </Box>
                            <Stack direction="row" spacing={1}>
                                <Button variant="outlined" onClick={() => void loadNumbers()}>
                                    Refresh
                                </Button>
                                <Button variant="contained" onClick={() => openNumberForm()}>
                                    Create Sequence
                                </Button>
                            </Stack>
                        </Stack>
                    </Paper>

                    <Collapse in={numberFormOpen}>
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField
                                        label="Prefix"
                                        value={numberForm.prefix}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, prefix: event.target.value }))
                                        }
                                        sx={{ minWidth: 120 }}
                                    />
                                    <TextField
                                        select
                                        label="Parent Account"
                                        value={numberForm.accounts_guid}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, accounts_guid: event.target.value }))
                                        }
                                        sx={{ minWidth: 260 }}
                                    >
                                        <MenuItem value="">Select account</MenuItem>
                                        {accounts.map((account) => (
                                            <MenuItem key={account.guid || account.number} value={account.guid || ""}>
                                                {account.number} — {account.name}
                                            </MenuItem>
                                        ))}
                                    </TextField>
                                    <TextField
                                        label="Account Number"
                                        value={numberForm.account_number}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, account_number: event.target.value }))
                                        }
                                        sx={{ minWidth: 160 }}
                                    />
                                    <TextField
                                        label="Scope"
                                        value={numberForm.scope}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, scope: event.target.value }))
                                        }
                                        sx={{ minWidth: 180 }}
                                    />
                                    <TextField
                                        select
                                        label="Sequence Type"
                                        value={numberForm.sequence_type}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, sequence_type: event.target.value }))
                                        }
                                        sx={{ minWidth: 180 }}
                                    >
                                        <MenuItem value="continuous">Continuous</MenuItem>
                                        <MenuItem value="non_continuous">Non-Continuous</MenuItem>
                                    </TextField>
                                    <TextField
                                        label="Series"
                                        value={numberForm.series_number}
                                        InputProps={{ readOnly: true }}
                                        sx={{ width: 120 }}
                                    />
                                    <TextField
                                        type="number"
                                        label="Last Number"
                                        value={numberForm.last_number}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, last_number: Number(event.target.value) }))
                                        }
                                        sx={{ width: 140 }}
                                    />
                                    <TextField
                                        type="number"
                                        label="Max Number"
                                        value={numberForm.max_number}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, max_number: Number(event.target.value) }))
                                        }
                                        sx={{ width: 160 }}
                                    />
                                    <TextField
                                        type="number"
                                        label="Allocation Size"
                                        value={numberForm.allocation_size}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, allocation_size: Number(event.target.value) }))
                                        }
                                        sx={{ width: 160 }}
                                    />
                                    <TextField
                                        label="Reset Policy"
                                        value={numberForm.reset_policy}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, reset_policy: event.target.value }))
                                        }
                                        sx={{ minWidth: 140 }}
                                    />
                                    <TextField
                                        select
                                        label="Status"
                                        value={numberForm.sequence_status}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({
                                                ...previous,
                                                sequence_status: Number(event.target.value),
                                            }))
                                        }
                                        sx={{ minWidth: 140 }}
                                    >
                                        <MenuItem value={1}>Active</MenuItem>
                                        <MenuItem value={0}>Inactive</MenuItem>
                                    </TextField>
                                </Stack>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField
                                        label="Pattern"
                                        value={numberForm.pattern}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, pattern: event.target.value }))
                                        }
                                        sx={{ minWidth: 300, flex: 1 }}
                                    />
                                    <TextField
                                        label="Display Format"
                                        value={numberForm.display_format}
                                        onChange={(event) =>
                                            setNumberForm((previous) => ({ ...previous, display_format: event.target.value }))
                                        }
                                        sx={{ minWidth: 240, flex: 1 }}
                                    />
                                </Stack>
                                <Stack direction="row" spacing={1}>
                                    <Button
                                        variant="contained"
                                        disabled={isBusy || !numberForm.accounts_guid || !numberForm.account_number.trim()}
                                        onClick={() => void saveNumber()}
                                    >
                                        Save
                                    </Button>
                                    <Button
                                        onClick={() => {
                                            setNumberForm(EMPTY_NUMBER_FORM);
                                            setNumberFormOpen(false);
                                        }}
                                    >
                                        Cancel
                                    </Button>
                                </Stack>
                            </Stack>
                        </Paper>
                    </Collapse>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Prefix</TableCell>
                                <TableCell>Account Number</TableCell>
                                <TableCell>Scope</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Series</TableCell>
                                <TableCell>Last</TableCell>
                                <TableCell>Allocation</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Pattern</TableCell>
                                <TableCell>Remaining</TableCell>
                                <TableCell align="right">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {numbers.map((item) => (
                                <TableRow key={item.recid || `${item.prefix}-${item.account_number}-${item.series_number}`}>
                                    <TableCell>{item.prefix || "—"}</TableCell>
                                    <TableCell>
                                        <Stack spacing={0.5}>
                                            <Typography variant="body2">{item.account_number}</Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                {item.account_name || "—"}
                                            </Typography>
                                        </Stack>
                                    </TableCell>
                                    <TableCell>{item.scope || "—"}</TableCell>
                                    <TableCell>
                                        <Chip
                                            color={getSequenceTypeColor(item.sequence_type)}
                                            label={getSequenceTypeLabel(item.sequence_type)}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{item.series_number}</TableCell>
                                    <TableCell>{item.last_number}</TableCell>
                                    <TableCell>{item.allocation_size}</TableCell>
                                    <TableCell>
                                        <Chip
                                            color={item.sequence_status === 1 ? "success" : "default"}
                                            label={item.sequence_status === 1 ? "Active" : "Inactive"}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>{item.pattern || item.display_format || "—"}</TableCell>
                                    <TableCell>{item.remaining ?? "—"}</TableCell>
                                    <TableCell align="right">
                                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                                            <Button size="small" onClick={() => openNumberForm(item)}>
                                                Edit
                                            </Button>
                                            <Button size="small" color="error" onClick={() => void deleteNumber(item)}>
                                                Delete
                                            </Button>
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {numbers.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={11}>
                                        <Typography variant="body2" color="text.secondary">
                                            No number sequences have been configured yet.
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 7 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                                <Box>
                                    <Typography variant="h6">Product Catalog</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Manage finance products and their customer-facing pricing metadata.
                                    </Typography>
                                </Box>
                                <Stack direction="row" spacing={1}>
                                    <Button variant="outlined" onClick={() => void loadProducts()}>Refresh</Button>
                                    <Button startIcon={<AddIcon />} variant="contained" onClick={openCreateProductDialog}>
                                        Add Product
                                    </Button>
                                </Stack>
                            </Stack>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>SKU</TableCell>
                                        <TableCell>Name</TableCell>
                                        <TableCell>Category</TableCell>
                                        <TableCell>Price</TableCell>
                                        <TableCell>Credits</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell align="right">Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {products.map((product) => (
                                        <TableRow key={product.recid}>
                                            <TableCell>{product.element_sku}</TableCell>
                                            <TableCell>{product.element_name}</TableCell>
                                            <TableCell>{PRODUCT_CATEGORY_LABELS[product.element_category] || product.element_category}</TableCell>
                                            <TableCell>{formatCurrency(product.element_price, product.element_currency)}</TableCell>
                                            <TableCell>{product.element_credits}</TableCell>
                                            <TableCell>
                                                <Chip
                                                    color={product.element_status === 1 ? "success" : "default"}
                                                    label={product.element_status === 1 ? "Active" : "Inactive"}
                                                />
                                            </TableCell>
                                            <TableCell align="right">
                                                <Stack direction="row" spacing={1} justifyContent="flex-end">
                                                    <Button size="small" onClick={() => openEditProductDialog(product)}>Edit</Button>
                                                    <Button size="small" color="error" onClick={() => setProductToDelete(product)}>Delete</Button>
                                                </Stack>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                    {products.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={7}>
                                                <Typography variant="body2" color="text.secondary">
                                                    No products have been configured yet.
                                                </Typography>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </Stack>
                    </Paper>

                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                                <Box>
                                    <Typography variant="h6">Journal Config Activation</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Activate approved product journal configurations so purchases can post into the correct journal.
                                    </Typography>
                                </Box>
                                <Button
                                    variant="outlined"
                                    onClick={() => void Promise.all([loadApprovedProductConfigs(), loadActiveProductConfigs(), loadProductConfigReferences()])}
                                >
                                    Refresh
                                </Button>
                            </Stack>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Category</TableCell>
                                        <TableCell>Journal Scope</TableCell>
                                        <TableCell>Journal</TableCell>
                                        <TableCell>Period</TableCell>
                                        <TableCell>Approved By</TableCell>
                                        <TableCell>Approved On</TableCell>
                                        <TableCell align="right">Actions</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {approvedProductConfigs.map((config) => (
                                        <TableRow key={config.recid}>
                                            <TableCell>{PRODUCT_CATEGORY_LABELS[config.element_category] || config.element_category}</TableCell>
                                            <TableCell>{config.element_journal_scope}</TableCell>
                                            <TableCell>
                                                {productConfigJournalByRecid.get(config.journals_recid)?.name || `Journal #${config.journals_recid}`}
                                            </TableCell>
                                            <TableCell>
                                                {productConfigPeriodByGuid.get(config.periods_guid)
                                                    ? `FY${productConfigPeriodByGuid.get(config.periods_guid)?.year} — ${productConfigPeriodByGuid.get(config.periods_guid)?.period_name}`
                                                    : config.periods_guid}
                                            </TableCell>
                                            <TableCell>{config.element_approved_by || "—"}</TableCell>
                                            <TableCell>{formatDateTime(config.element_approved_on)}</TableCell>
                                            <TableCell align="right">
                                                <Button
                                                    variant="contained"
                                                    size="small"
                                                    onClick={async () => {
                                                        try {
                                                            setPageError(null);
                                                            setSuccessMessage(null);
                                                            await fetchPjcActivate({ recid: config.recid });
                                                            setSuccessMessage(`Activated product journal configuration ${config.recid}.`);
                                                            await Promise.all([loadApprovedProductConfigs(), loadActiveProductConfigs()]);
                                                        } catch (error: unknown) {
                                                            setPageError(getErrorMessage(error));
                                                        }
                                                    }}
                                                >
                                                    Activate
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                    {approvedProductConfigs.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={7}>
                                                <Typography variant="body2" color="text.secondary">
                                                    No approved product journal configurations are waiting for activation.
                                                </Typography>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>

                            <Box>
                                <Typography variant="subtitle1" sx={{ mb: 1 }}>Active Configurations</Typography>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Category</TableCell>
                                            <TableCell>Journal Scope</TableCell>
                                            <TableCell>Journal</TableCell>
                                            <TableCell>Period</TableCell>
                                            <TableCell>Approved By</TableCell>
                                            <TableCell>Status</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {activeProductConfigs.map((config) => (
                                            <TableRow key={config.recid}>
                                                <TableCell>{PRODUCT_CATEGORY_LABELS[config.element_category] || config.element_category}</TableCell>
                                                <TableCell>{config.element_journal_scope}</TableCell>
                                                <TableCell>
                                                    {productConfigJournalByRecid.get(config.journals_recid)?.name || `Journal #${config.journals_recid}`}
                                                </TableCell>
                                                <TableCell>
                                                    {productConfigPeriodByGuid.get(config.periods_guid)
                                                        ? `FY${productConfigPeriodByGuid.get(config.periods_guid)?.year} — ${productConfigPeriodByGuid.get(config.periods_guid)?.period_name}`
                                                        : config.periods_guid}
                                                </TableCell>
                                                <TableCell>{config.element_approved_by || "—"}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={PRODUCT_JOURNAL_CONFIG_STATUS[config.element_status]?.label || `Status ${config.element_status}`}
                                                        color={PRODUCT_JOURNAL_CONFIG_STATUS[config.element_status]?.color || "default"}
                                                    />
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                        {activeProductConfigs.length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={6}>
                                                    <Typography variant="body2" color="text.secondary">
                                                        No active product journal configurations are available.
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </Box>
                        </Stack>
                    </Paper>
                </Stack>
            )}

            <Dialog fullWidth maxWidth="sm" open={productFormOpen} onClose={closeProductFormDialog}>
                <DialogTitle>{productForm.recid === null ? "Add product" : "Edit product"}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            autoFocus
                            required
                            label="SKU"
                            value={productForm.element_sku}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_sku: event.target.value }))}
                        />
                        <TextField
                            required
                            label="Name"
                            value={productForm.element_name}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_name: event.target.value }))}
                        />
                        <TextField
                            label="Description"
                            multiline
                            minRows={3}
                            value={productForm.element_description}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_description: event.target.value }))}
                        />
                        <TextField
                            select
                            label="Category"
                            value={productForm.element_category}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_category: event.target.value }))}
                        >
                            {productCategoryOptions.map((category) => (
                                <MenuItem key={category} value={category}>
                                    {PRODUCT_CATEGORY_LABELS[category] || category}
                                </MenuItem>
                            ))}
                        </TextField>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                            <TextField
                                label="Price"
                                value={productForm.element_price}
                                onChange={(event) => setProductForm((previous) => ({ ...previous, element_price: event.target.value }))}
                                fullWidth
                            />
                            <TextField
                                label="Currency"
                                value={productForm.element_currency}
                                onChange={(event) => setProductForm((previous) => ({ ...previous, element_currency: event.target.value.toUpperCase() }))}
                                fullWidth
                            />
                        </Stack>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                            <TextField
                                type="number"
                                label="Credits"
                                value={productForm.element_credits}
                                onChange={(event) =>
                                    setProductForm((previous) => ({ ...previous, element_credits: Number(event.target.value) || 0 }))
                                }
                                fullWidth
                            />
                            <TextField
                                type="number"
                                label="Sort Order"
                                value={productForm.element_sort_order}
                                onChange={(event) =>
                                    setProductForm((previous) => ({ ...previous, element_sort_order: Number(event.target.value) || 0 }))
                                }
                                fullWidth
                            />
                        </Stack>
                        <TextField
                            label="Enablement Key"
                            value={productForm.element_enablement_key}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_enablement_key: event.target.value }))}
                        />
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={productForm.element_is_recurring}
                                    onChange={(event) =>
                                        setProductForm((previous) => ({ ...previous, element_is_recurring: event.target.checked }))
                                    }
                                />
                            }
                            label="Recurring product"
                        />
                        <TextField
                            select
                            label="Status"
                            value={productForm.element_status}
                            onChange={(event) => setProductForm((previous) => ({ ...previous, element_status: Number(event.target.value) }))}
                        >
                            <MenuItem value={1}>Active</MenuItem>
                            <MenuItem value={0}>Inactive</MenuItem>
                        </TextField>
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeProductFormDialog}>Cancel</Button>
                    <Button
                        variant="contained"
                        disabled={isBusy || !productForm.element_sku.trim() || !productForm.element_name.trim() || !productForm.element_category.trim()}
                        onClick={() => void saveProduct()}
                    >
                        Save
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={productToDelete !== null} onClose={() => setProductToDelete(null)} fullWidth maxWidth="xs">
                <DialogTitle>Delete product</DialogTitle>
                <DialogContent>
                    <Typography variant="body2">
                        {productToDelete
                            ? `Delete product ${productToDelete.element_sku} — ${productToDelete.element_name}?`
                            : "Delete this product?"}
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setProductToDelete(null)}>Cancel</Button>
                    <Button color="error" variant="contained" disabled={isBusy || !productToDelete} onClick={() => void confirmDeleteProduct()}>
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog fullWidth maxWidth="sm" open={ledgerDialogOpen} onClose={closeLedgerDialog}>
                <DialogTitle>{ledgerForm.recid === null ? "Create ledger" : "Edit ledger"}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            autoFocus
                            required
                            label="Ledger name"
                            value={ledgerForm.element_name}
                            onChange={(event) =>
                                setLedgerForm((previous) => ({ ...previous, element_name: event.target.value }))
                            }
                        />
                        <TextField
                            label="Description"
                            value={ledgerForm.element_description}
                            onChange={(event) =>
                                setLedgerForm((previous) => ({ ...previous, element_description: event.target.value }))
                            }
                            multiline
                            minRows={2}
                        />
                        <FormControl fullWidth>
                            <InputLabel id="ledger-coa-label">Chart of accounts root</InputLabel>
                            <Select
                                labelId="ledger-coa-label"
                                label="Chart of accounts root"
                                value={ledgerForm.element_chart_of_accounts_guid}
                                onChange={(event) =>
                                    setLedgerForm((previous) => ({
                                        ...previous,
                                        element_chart_of_accounts_guid: String(event.target.value),
                                    }))
                                }
                            >
                                <MenuItem value="">
                                    <em>None</em>
                                </MenuItem>
                                {accounts.map((account) => (
                                    <MenuItem key={account.guid || account.number} value={account.guid || ""}>
                                        {account.number} — {account.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        {ledgerForm.recid !== null && (
                            <FormControl fullWidth>
                                <InputLabel id="ledger-status-label">Status</InputLabel>
                                <Select
                                    labelId="ledger-status-label"
                                    label="Status"
                                    value={ledgerForm.element_status}
                                    onChange={(event) =>
                                        setLedgerForm((previous) => ({
                                            ...previous,
                                            element_status: Number(event.target.value),
                                        }))
                                    }
                                >
                                    {LEDGER_STATUS_OPTIONS.map((option) => (
                                        <MenuItem key={option.value} value={option.value}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeLedgerDialog}>Cancel</Button>
                    <Button variant="contained" disabled={isBusy || !ledgerForm.element_name.trim()} onClick={() => void submitLedger()}>
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default FinanceAdminPage;
