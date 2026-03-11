import { useEffect, useState } from "react";
import {
        Box,
        Checkbox,
        Divider,
        IconButton,
        MenuItem,
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableRow,
        TextField,
        Typography,
} from "@mui/material";
import { Add, Delete } from "@mui/icons-material";

import ColumnHeader from "../../components/ColumnHeader";
import EditBox from "../../components/EditBox";
import PageTitle from "../../components/PageTitle";
import {
        fetchDeleteModel,
        fetchModels,
        fetchUpsertModel,
} from "../../rpc/system/models";
import type {
        SystemModelsList1,
        SystemModelsModelItem1,
        SystemModelsUpsertModel1,
} from "../../shared/RpcModels";

const SystemModelsPage = (): JSX.Element => {
        const [models, setModels] = useState<SystemModelsModelItem1[]>([]);
        const [apiProviders, setApiProviders] = useState<string[]>(["openai", "lumalabs"]);
        const [newModel, setNewModel] = useState<SystemModelsUpsertModel1>({
                recid: null,
                name: "",
                api_provider: "openai",
                is_active: true,
        });
        const [forbidden, setForbidden] = useState(false);

        const load = async (): Promise<void> => {
                try {
                        const res: SystemModelsList1 = await fetchModels();
                        const sorted = [...(res.models ?? [])].sort((a, b) => a.name.localeCompare(b.name));
                        setModels(sorted);
                        setApiProviders(res.api_providers?.length ? res.api_providers : ["openai", "lumalabs"]);
                        setNewModel((prev) => ({
                                ...prev,
                                recid: null,
                                api_provider: prev.api_provider || "openai",
                        }));
                        setForbidden(false);
                } catch (e: any) {
                        if (e?.response?.status === 403) {
                                setForbidden(true);
                        } else {
                                setModels([]);
                        }
                }
        };

        useEffect(() => {
                void load();
        }, []);

        if (forbidden) {
                return (
                        <Box sx={{ p: 2 }}>
                                <Typography variant="h6">Forbidden</Typography>
                        </Box>
                );
        }

        const updateModel = async (
                index: number,
                changes: Partial<SystemModelsModelItem1>,
        ): Promise<void> => {
                const updated = [...models];
                const next = { ...updated[index], ...changes };
                updated[index] = next;
                setModels(updated);
                await fetchUpsertModel({
                        recid: next.recid ?? null,
                        name: next.name,
                        api_provider: next.api_provider,
                        is_active: next.is_active,
                });
                void load();
        };

        const handleDelete = async (item: SystemModelsModelItem1): Promise<void> => {
                await fetchDeleteModel({
                        recid: item.recid ?? null,
                        name: item.name,
                });
                void load();
        };

        const handleAdd = async (): Promise<void> => {
                if (!newModel.name.trim()) return;
                await fetchUpsertModel({
                        recid: null,
                        name: newModel.name.trim(),
                        api_provider: newModel.api_provider,
                        is_active: Boolean(newModel.is_active),
                });
                setNewModel({
                        recid: null,
                        name: "",
                        api_provider: apiProviders.length ? apiProviders[0] : "openai",
                        is_active: true,
                });
                void load();
        };

        return (
                <Box sx={{ p: 2 }}>
                        <PageTitle>System Models</PageTitle>
                        <Divider sx={{ mb: 2 }} />
                        <Table size="small" sx={{ "& td, & th": { py: 0.5, verticalAlign: "top" } }}>
                                <TableHead>
                                        <TableRow>
                                                <ColumnHeader sx={{ width: "45%" }}>Model Name</ColumnHeader>
                                                <ColumnHeader sx={{ width: "30%" }}>API Provider</ColumnHeader>
                                                <ColumnHeader sx={{ width: "15%" }}>Active</ColumnHeader>
                                                <ColumnHeader sx={{ width: "10%" }}>Actions</ColumnHeader>
                                        </TableRow>
                                </TableHead>
                                <TableBody>
                                        {models.map((model, index) => (
                                                <TableRow key={model.recid}>
                                                        <TableCell sx={{ width: "45%" }}>
                                                                <EditBox
                                                                        value={model.name}
                                                                        onCommit={(value) =>
                                                                                void updateModel(index, { name: String(value) })
                                                                        }
                                                                />
                                                        </TableCell>
                                                        <TableCell sx={{ width: "30%" }}>
                                                                <TextField
                                                                        select
                                                                        sx={{ width: "95%" }}
                                                                        value={model.api_provider}
                                                                        onChange={(e) =>
                                                                                void updateModel(index, {
                                                                                        api_provider: e.target.value,
                                                                                })
                                                                        }
                                                                >
                                                                        {apiProviders.map((provider) => (
                                                                                <MenuItem key={provider} value={provider}>
                                                                                        {provider}
                                                                                </MenuItem>
                                                                        ))}
                                                                </TextField>
                                                        </TableCell>
                                                        <TableCell sx={{ width: "15%" }}>
                                                                <Checkbox
                                                                        checked={Boolean(model.is_active)}
                                                                        onChange={(e) =>
                                                                                void updateModel(index, {
                                                                                        is_active: e.target.checked,
                                                                                })
                                                                        }
                                                                />
                                                        </TableCell>
                                                        <TableCell sx={{ width: "10%" }}>
                                                                <IconButton onClick={() => void handleDelete(model)}>
                                                                        <Delete />
                                                                </IconButton>
                                                        </TableCell>
                                                </TableRow>
                                        ))}
                                        <TableRow>
                                                <TableCell sx={{ width: "45%" }}>
                                                        <TextField
                                                                sx={{ width: "95%" }}
                                                                value={newModel.name}
                                                                placeholder="Model Name"
                                                                onChange={(e) =>
                                                                        setNewModel({
                                                                                ...newModel,
                                                                                name: e.target.value,
                                                                        })
                                                                }
                                                        />
                                                </TableCell>
                                                <TableCell sx={{ width: "30%" }}>
                                                        <TextField
                                                                select
                                                                sx={{ width: "95%" }}
                                                                value={newModel.api_provider}
                                                                onChange={(e) =>
                                                                        setNewModel({
                                                                                ...newModel,
                                                                                api_provider: e.target.value,
                                                                        })
                                                                }
                                                        >
                                                                {apiProviders.map((provider) => (
                                                                        <MenuItem key={provider} value={provider}>
                                                                                {provider}
                                                                        </MenuItem>
                                                                ))}
                                                        </TextField>
                                                </TableCell>
                                                <TableCell sx={{ width: "15%" }}>
                                                        <Checkbox
                                                                checked={Boolean(newModel.is_active)}
                                                                onChange={(e) =>
                                                                        setNewModel({
                                                                                ...newModel,
                                                                                is_active: e.target.checked,
                                                                        })
                                                                }
                                                        />
                                                </TableCell>
                                                <TableCell sx={{ width: "10%" }}>
                                                        <IconButton onClick={() => void handleAdd()}>
                                                                <Add />
                                                        </IconButton>
                                                </TableCell>
                                        </TableRow>
                                </TableBody>
                        </Table>
                </Box>
        );
};

export default SystemModelsPage;
