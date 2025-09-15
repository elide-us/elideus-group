import { useEffect, useState } from "react";
import {
        Box,
        Divider,
        Table,
        TableHead,
        TableRow,
        TableCell,
        TableBody,
        Typography,
        IconButton,
        TextField,
        MenuItem,
} from "@mui/material";
import { Delete, Add } from "@mui/icons-material";
import PageTitle from "../components/PageTitle";
import EditBox from "../components/EditBox";
import ColumnHeader from "../components/ColumnHeader";
import type {
        DiscordPersonasPersonaItem1,
        DiscordPersonasList1,
        DiscordPersonasModels1,
        DiscordPersonasModelItem1,
        DiscordPersonasUpsertPersona1,
} from "../shared/RpcModels";
import {
        fetchPersonas,
        fetchModels,
        fetchUpsertPersona,
        fetchDeletePersona,
} from "../rpc/discord/personas";

const DiscordPersonasPage = (): JSX.Element => {
        const [personas, setPersonas] = useState<DiscordPersonasPersonaItem1[]>([]);
        const [models, setModels] = useState<DiscordPersonasModelItem1[]>([]);
        const [newPersona, setNewPersona] = useState<DiscordPersonasUpsertPersona1>({
                recid: null,
                name: "",
                prompt: "",
                tokens: 0,
                models_recid: 0,
        });
        const [forbidden, setForbidden] = useState(false);

        const load = async (): Promise<void> => {
                try {
                        const res: DiscordPersonasList1 = await fetchPersonas();
                        const sorted = [...(res.personas ?? [])].sort((a, b) => a.name.localeCompare(b.name));
                        setPersonas(sorted);
                        setForbidden(false);
                } catch (e: any) {
                        if (e?.response?.status === 403) {
                                setForbidden(true);
                        } else {
                                setPersonas([]);
                        }
                }
                try {
                        const resModels: DiscordPersonasModels1 = await fetchModels();
                        setModels(resModels.models ?? []);
                        setNewPersona((prev) => ({
                                ...prev,
                                recid: null,
                                models_recid:
                                        prev.models_recid || (resModels.models && resModels.models.length ? resModels.models[0].recid : 0),
                        }));
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

        const updatePersona = async (
                index: number,
                changes: Partial<DiscordPersonasPersonaItem1>,
        ): Promise<void> => {
                const updated = [...personas];
                const next = { ...updated[index], ...changes };
                updated[index] = next;
                setPersonas(updated);
                await fetchUpsertPersona({
                        recid: next.recid ?? null,
                        name: next.name,
                        prompt: next.prompt,
                        tokens: next.tokens,
                        models_recid: next.models_recid,
                });
                void load();
        };

        const handleDelete = async (item: DiscordPersonasPersonaItem1): Promise<void> => {
                await fetchDeletePersona({
                        recid: item.recid ?? null,
                        name: item.name,
                });
                void load();
        };

        const handleAdd = async (): Promise<void> => {
                if (!newPersona.name.trim()) return;
                if (!newPersona.models_recid) return;
                await fetchUpsertPersona({
                        recid: null,
                        name: newPersona.name.trim(),
                        prompt: newPersona.prompt,
                        tokens: newPersona.tokens,
                        models_recid: newPersona.models_recid,
                });
                setNewPersona({
                        recid: null,
                        name: "",
                        prompt: "",
                        tokens: 0,
                        models_recid: models.length ? models[0].recid : 0,
                });
                void load();
        };

        return (
                <Box sx={{ p: 2 }}>
                        <PageTitle>Persona Editor</PageTitle>
                        <Divider sx={{ mb: 2 }} />
                        <Table size="small" sx={{ "& td, & th": { py: 0.5, verticalAlign: "top" } }}>
                                <TableHead>
                                        <TableRow>
                                                <ColumnHeader sx={{ width: "15%" }}>Persona</ColumnHeader>
                                                <ColumnHeader sx={{ width: "15%" }}>Model</ColumnHeader>
                                                <ColumnHeader sx={{ width: "10%" }}>Tokens</ColumnHeader>
                                                <ColumnHeader sx={{ width: "55%" }}>Prompt</ColumnHeader>
                                                <ColumnHeader sx={{ width: "5%" }} />
                                        </TableRow>
                                </TableHead>
                                <TableBody>
                                        {personas.map((persona, idx) => (
                                                <TableRow key={`${persona.name}-${persona.recid ?? idx}`}>
                                                        <TableCell sx={{ width: "15%" }}>
                                                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                                                        {persona.name}
                                                                </Typography>
                                                        </TableCell>
                                                        <TableCell sx={{ width: "15%" }}>
                                                                <TextField
                                                                        select
                                                                        sx={{ width: "95%" }}
                                                                        value={persona.models_recid}
                                                                        onChange={(e) => {
                                                                                const value = Number(e.target.value);
                                                                                const modelName = models.find((m) => m.recid === value)?.name ?? persona.model;
                                                                                void updatePersona(idx, {
                                                                                        models_recid: value,
                                                                                        model: modelName,
                                                                                });
                                                                        }}
                                                                >
                                                                        {models.map((model) => (
                                                                                <MenuItem key={model.recid} value={model.recid}>
                                                                                        {model.name}
                                                                                </MenuItem>
                                                                        ))}
                                                                </TextField>
                                                        </TableCell>
                                                        <TableCell sx={{ width: "10%" }}>
                                                                <EditBox
                                                                        value={persona.tokens}
                                                                        onCommit={(val) => updatePersona(idx, { tokens: Number(val) })}
                                                                        width="80px"
                                                                />
                                                        </TableCell>
                                                        <TableCell sx={{ width: "55%" }}>
                                                                <EditBox
                                                                        value={persona.prompt}
                                                                        onCommit={(val) => updatePersona(idx, { prompt: String(val) })}
                                                                        width="100%"
                                                                />
                                                        </TableCell>
                                                        <TableCell sx={{ width: "5%" }}>
                                                                <IconButton onClick={() => void handleDelete(persona)}>
                                                                        <Delete />
                                                                </IconButton>
                                                        </TableCell>
                                                </TableRow>
                                        ))}
                                        <TableRow>
                                                <TableCell sx={{ width: "15%" }}>
                                                        <TextField
                                                                sx={{ width: "95%" }}
                                                                value={newPersona.name}
                                                                placeholder="Name"
                                                                onChange={(e) =>
                                                                        setNewPersona({
                                                                                ...newPersona,
                                                                                name: e.target.value,
                                                                        })
                                                                }
                                                        />
                                                </TableCell>
                                                <TableCell sx={{ width: "15%" }}>
                                                        <TextField
                                                                select
                                                                sx={{ width: "95%" }}
                                                                value={newPersona.models_recid}
                                                                onChange={(e) =>
                                                                        setNewPersona({
                                                                                ...newPersona,
                                                                                models_recid: Number(e.target.value),
                                                                        })
                                                                }
                                                        >
                                                                {models.map((model) => (
                                                                        <MenuItem key={model.recid} value={model.recid}>
                                                                                {model.name}
                                                                        </MenuItem>
                                                                ))}
                                                        </TextField>
                                                </TableCell>
                                                <TableCell sx={{ width: "10%" }}>
                                                        <TextField
                                                                type="number"
                                                                sx={{ width: "80px" }}
                                                                value={newPersona.tokens}
                                                                onChange={(e) =>
                                                                        setNewPersona({
                                                                                ...newPersona,
                                                                                tokens: Number(e.target.value),
                                                                        })
                                                                }
                                                        />
                                                </TableCell>
                                                <TableCell sx={{ width: "55%" }}>
                                                        <TextField
                                                                sx={{ width: "100%" }}
                                                                value={newPersona.prompt}
                                                                onChange={(e) =>
                                                                        setNewPersona({
                                                                                ...newPersona,
                                                                                prompt: e.target.value,
                                                                        })
                                                                }
                                                        />
                                                </TableCell>
                                                <TableCell sx={{ width: "5%" }}>
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

export default DiscordPersonasPage;
