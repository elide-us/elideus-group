import { useEffect, useState } from "react";
import {
    Box,
    Table,
    TableHead,
    TableRow,
    TableCell,
    TableBody,
    IconButton,
    TextField,
    Typography,
} from "@mui/material";
import { Delete, Add } from "@mui/icons-material";
import type {
    SystemConfigConfigItem1,
    SystemConfigList1,
} from "./shared/RpcModels";
import {
    fetchConfigs,
    fetchUpsertConfig,
    fetchDeleteConfig,
} from "./rpc/system/config";
import Notification from "./Notification";

const SystemConfigPage = (): JSX.Element => {
    const [items, setItems] = useState<SystemConfigConfigItem1[]>([]);
    const [newItem, setNewItem] = useState<SystemConfigConfigItem1>({
        key: "",
        value: "",
    });
    const [notification, setNotification] = useState(false);
    const [forbidden, setForbidden] = useState(false);
    const handleNotificationClose = (): void => {
        setNotification(false);
    };

    const load = async (): Promise<void> => {
        try {
            const res: SystemConfigList1 = await fetchConfigs();
            setItems(res.items);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            } else {
                setItems([]);
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

    const updateItem = async (
        index: number,
        field: keyof SystemConfigConfigItem1,
        value: string,
    ): Promise<void> => {
        const updated = [...items];
        (updated[index] as any)[field] = value;
        setItems(updated);
        await fetchUpsertConfig(updated[index]);
        setNotification(true);
    };

    const handleDelete = async (key: string): Promise<void> => {
        await fetchDeleteConfig({ key });
        void load();
        setNotification(true);
    };

    const handleAdd = async (): Promise<void> => {
        if (!newItem.key) return;
        await fetchUpsertConfig(newItem);
        setNewItem({ key: "", value: "" });
        void load();
        setNotification(true);
    };

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h5">System Configuration</Typography>
            <Table size="small" sx={{ "& td, & th": { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <TableCell>Key</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {items.map((i, idx) => (
                        <TableRow key={i.key}>
                            <TableCell>
                                <TextField
                                    value={i.key}
                                    onChange={(e) => updateItem(idx, "key", e.target.value)}
                                />
                            </TableCell>
                            <TableCell>
                                <TextField
                                    value={i.value}
                                    onChange={(e) => updateItem(idx, "value", e.target.value)}
                                />
                            </TableCell>
                            <TableCell>
                                <IconButton onClick={() => void handleDelete(i.key)}>
                                    <Delete />
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                    <TableRow>
                        <TableCell>
                            <TextField
                                value={newItem.key}
                                onChange={(e) => setNewItem({ ...newItem, key: e.target.value })}
                            />
                        </TableCell>
                        <TableCell>
                            <TextField
                                value={newItem.value}
                                onChange={(e) => setNewItem({ ...newItem, value: e.target.value })}
                            />
                        </TableCell>
                        <TableCell>
                            <IconButton onClick={() => void handleAdd()}>
                                <Add />
                            </IconButton>
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity="success"
                message="Saved"
            />
        </Box>
    );
};

export default SystemConfigPage;
