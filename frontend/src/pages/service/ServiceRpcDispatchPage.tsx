import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Box,
    Button,
    Chip,
    Paper,
    Stack,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Tabs,
    Typography,
} from '@mui/material';
import PageTitle from '../../components/PageTitle';
import { rpcCall } from '../../shared/RpcModels';

type DomainItem = {
    recid: number;
    element_name: string;
    element_required_role: string | null;
    element_is_auth_exempt: boolean;
    element_is_public: boolean;
    element_is_discord: boolean;
    element_status: number;
    element_app_version: string | null;
    element_iteration: number;
};

type SubdomainItem = {
    recid: number;
    domains_recid: number;
    element_name: string;
    element_entitlement_mask: number;
    element_status: number;
    element_app_version: string | null;
    element_iteration: number;
};

type FunctionItem = {
    recid: number;
    subdomains_recid: number;
    element_name: string;
    element_version: number;
    element_module_attr: string;
    element_method_name: string;
    element_request_model_recid: number | null;
    element_response_model_recid: number | null;
    element_status: number;
};

type ModelItem = {
    recid: number;
    element_name: string;
    element_domain: string;
    element_subdomain: string;
    element_version: number;
    element_parent_recid: number | null;
    element_status: number;
    element_app_version: string | null;
};

type ModelFieldItem = {
    recid: number;
    models_recid: number;
    element_name: string;
    element_edt_recid: number | null;
    element_is_nullable: boolean;
    element_is_list: boolean;
    element_is_dict: boolean;
    element_ref_model_recid: number | null;
    element_default_value: string | null;
    element_sort_order: number;
};

const EDT_NAME_BY_RECID: Record<number, string> = {
    1: 'INT32',
    2: 'INT64',
    3: 'INT64_IDENTITY',
    4: 'UUID',
    5: 'BOOL',
    7: 'DATETIME_TZ',
    8: 'STRING',
    9: 'TEXT',
    11: 'INT8',
    12: 'DATE',
    13: 'DECIMAL_19_5',
};

const boolChip = (value: boolean): JSX.Element =>
    value ? <Chip label="Yes" color="success" size="small" /> : <Chip label="No" size="small" />;

const statusChip = (status: number): JSX.Element =>
    status === 1 ? <Chip label="Active" color="success" size="small" /> : <Chip label="Disabled" size="small" />;

const emptyValue = (value: string | number | null | undefined): string | number => {
    if (value === null || value === undefined || value === '') {
        return '—';
    }
    return value;
};

const ServiceRpcDispatchPage = (): JSX.Element => {
    const [tabIndex, setTabIndex] = useState(0);
    const [forbidden, setForbidden] = useState(false);

    const [domains, setDomains] = useState<DomainItem[]>([]);
    const [subdomains, setSubdomains] = useState<SubdomainItem[]>([]);
    const [functions, setFunctions] = useState<FunctionItem[]>([]);
    const [models, setModels] = useState<ModelItem[]>([]);
    const [fields, setFields] = useState<ModelFieldItem[]>([]);

    const [loading, setLoading] = useState(false);

    const domainMap = useMemo(() => new Map(domains.map((d) => [d.recid, d.element_name])), [domains]);
    const subdomainMap = useMemo(() => new Map(subdomains.map((s) => [s.recid, s.element_name])), [subdomains]);
    const modelMap = useMemo(() => new Map(models.map((m) => [m.recid, m.element_name])), [models]);

    const handleRpcError = (error: any): never => {
        if (error?.response?.status === 403) {
            setForbidden(true);
        }
        throw error;
    };

    const loadDomains = useCallback(async (): Promise<void> => {
        try {
            const response = await rpcCall<{ domains: DomainItem[] }>('urn:service:rpcdispatch:list_domains:1');
            setDomains(response.domains || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadSubdomains = useCallback(async (): Promise<void> => {
        try {
            const response = await rpcCall<{ subdomains: SubdomainItem[] }>('urn:service:rpcdispatch:list_subdomains:1');
            setSubdomains(response.subdomains || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadFunctions = useCallback(async (): Promise<void> => {
        try {
            const response = await rpcCall<{ functions: FunctionItem[] }>('urn:service:rpcdispatch:list_functions:1');
            setFunctions(response.functions || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadModels = useCallback(async (): Promise<void> => {
        try {
            const response = await rpcCall<{ models: ModelItem[] }>('urn:service:rpcdispatch:list_models:1');
            setModels(response.models || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadModelFields = useCallback(async (): Promise<void> => {
        try {
            const response = await rpcCall<{ fields: ModelFieldItem[] }>('urn:service:rpcdispatch:list_model_fields:1');
            setFields(response.fields || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadAll = useCallback(async (): Promise<void> => {
        setLoading(true);
        try {
            await Promise.all([loadDomains(), loadSubdomains(), loadFunctions(), loadModels(), loadModelFields()]);
        } finally {
            setLoading(false);
        }
    }, [loadDomains, loadFunctions, loadModelFields, loadModels, loadSubdomains]);

    const refreshActiveTab = useCallback(async (): Promise<void> => {
        setLoading(true);
        try {
            if (tabIndex === 0) {
                await loadDomains();
            } else if (tabIndex === 1) {
                await loadSubdomains();
            } else if (tabIndex === 2) {
                await loadFunctions();
            } else if (tabIndex === 3) {
                await loadModels();
            } else {
                await loadModelFields();
            }
        } finally {
            setLoading(false);
        }
    }, [loadDomains, loadFunctions, loadModelFields, loadModels, loadSubdomains, tabIndex]);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    useEffect(() => {
        void refreshActiveTab();
    }, [tabIndex, refreshActiveTab]);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>RPC Dispatch</PageTitle>

            <Paper sx={{ p: 2, mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                        Read-only service view of reflection_rpc_* metadata tables.
                    </Typography>
                    <Button variant="outlined" onClick={() => void refreshActiveTab()} disabled={loading}>
                        Refresh
                    </Button>
                </Stack>
            </Paper>

            <Paper>
                <Tabs value={tabIndex} onChange={(_, value: number) => setTabIndex(value)} variant="scrollable">
                    <Tab label={`Domains (${domains.length})`} />
                    <Tab label={`Subdomains (${subdomains.length})`} />
                    <Tab label={`Functions (${functions.length})`} />
                    <Tab label={`Models (${models.length})`} />
                    <Tab label={`Model Fields (${fields.length})`} />
                </Tabs>

                <Box sx={{ p: 2 }}>
                    {tabIndex === 0 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Required Role</TableCell>
                                    <TableCell>Auth Exempt</TableCell>
                                    <TableCell>Public</TableCell>
                                    <TableCell>Discord</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                    <TableCell>Iteration</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {domains.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{emptyValue(row.element_required_role)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_auth_exempt)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_public)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_discord)}</TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                        <TableCell>{row.element_iteration}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 1 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Domain</TableCell>
                                    <TableCell>Entitlement Mask</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                    <TableCell>Iteration</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {subdomains.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{domainMap.get(row.domains_recid) ?? `#${row.domains_recid}`}</TableCell>
                                        <TableCell>{row.element_entitlement_mask}</TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                        <TableCell>{row.element_iteration}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 2 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Version</TableCell>
                                    <TableCell>Subdomain</TableCell>
                                    <TableCell>Module Attr</TableCell>
                                    <TableCell>Method Name</TableCell>
                                    <TableCell>Request Model</TableCell>
                                    <TableCell>Response Model</TableCell>
                                    <TableCell>Status</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {functions.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{row.element_version}</TableCell>
                                        <TableCell>{subdomainMap.get(row.subdomains_recid) ?? `#${row.subdomains_recid}`}</TableCell>
                                        <TableCell>{row.element_module_attr}</TableCell>
                                        <TableCell>{row.element_method_name}</TableCell>
                                        <TableCell>
                                            {row.element_request_model_recid
                                                ? modelMap.get(row.element_request_model_recid) ??
                                                  `#${row.element_request_model_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>
                                            {row.element_response_model_recid
                                                ? modelMap.get(row.element_response_model_recid) ??
                                                  `#${row.element_response_model_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 3 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Domain</TableCell>
                                    <TableCell>Subdomain</TableCell>
                                    <TableCell>Version</TableCell>
                                    <TableCell>Parent</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {models.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{row.element_domain}</TableCell>
                                        <TableCell>{row.element_subdomain}</TableCell>
                                        <TableCell>{row.element_version}</TableCell>
                                        <TableCell>
                                            {row.element_parent_recid
                                                ? modelMap.get(row.element_parent_recid) ?? `#${row.element_parent_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 4 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Field Name</TableCell>
                                    <TableCell>Model</TableCell>
                                    <TableCell>EDT</TableCell>
                                    <TableCell>Nullable</TableCell>
                                    <TableCell>List</TableCell>
                                    <TableCell>Dict</TableCell>
                                    <TableCell>Ref Model</TableCell>
                                    <TableCell>Default Value</TableCell>
                                    <TableCell>Sort Order</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {fields.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{modelMap.get(row.models_recid) ?? `#${row.models_recid}`}</TableCell>
                                        <TableCell>
                                            {row.element_edt_recid
                                                ? EDT_NAME_BY_RECID[row.element_edt_recid] ?? `#${row.element_edt_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{boolChip(row.element_is_nullable)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_list)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_dict)}</TableCell>
                                        <TableCell>
                                            {row.element_ref_model_recid
                                                ? modelMap.get(row.element_ref_model_recid) ??
                                                  `#${row.element_ref_model_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{emptyValue(row.element_default_value)}</TableCell>
                                        <TableCell>{row.element_sort_order}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </Box>
            </Paper>
        </Box>
    );
};

export default ServiceRpcDispatchPage;
