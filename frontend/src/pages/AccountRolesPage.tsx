import { useEffect, useState } from "react";
import {
    Box,
    Stack,
    List,
    ListItemButton,
    ListItemText,
    IconButton,
    Typography,
} from "@mui/material";
import { ArrowForwardIos, ArrowBackIos } from "@mui/icons-material";
import PageTitle from "../components/PageTitle";
import type {
    AccountRoleAggregateItem1,
    AccountRoleAggregateList1,
} from "../shared/RpcModels";
import {
    fetchAllRoleMembers,
    fetchAddRoleMember,
    fetchRemoveRoleMember,
} from "../rpc/account/role";

const AccountRolesPage = (): JSX.Element => {
    const [roles, setRoles] = useState<AccountRoleAggregateItem1[]>([]);
    const [selectedLeft, setSelectedLeft] = useState<Record<string, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<string, string>>({});

    const load = async (): Promise<void> => {
        try {
            const res: AccountRoleAggregateList1 = await fetchAllRoleMembers();
            const sorted = [...res.roles].sort((a, b) => {
                const am = BigInt(a.mask);
                const bm = BigInt(b.mask);
                if (am < bm) return -1;
                if (am > bm) return 1;
                return 0;
            });
            setRoles(sorted);
        } catch {
            setRoles([]);
        }
    };

    useEffect(() => {
        void load();
    }, []);

    const moveRight = async (role: string): Promise<void> => {
        const id = selectedLeft[role];
        if (!id) return;
        await fetchAddRoleMember({ role, userGuid: id });
        setSelectedLeft((s) => ({ ...s, [role]: "" }));
        void load();
    };

    const moveLeft = async (role: string): Promise<void> => {
        const id = selectedRight[role];
        if (!id) return;
        await fetchRemoveRoleMember({ role, userGuid: id });
        setSelectedRight((s) => ({ ...s, [role]: "" }));
        void load();
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Account Roles</PageTitle>
            <Stack spacing={2}>
                {roles.map((role) => (
                    <Stack key={role.name} spacing={2} direction="column" alignItems="center">
                        <Typography variant="h6">{role.name}</Typography>
                        <Stack direction="row" spacing={1}>
                            <List
                                sx={{
                                    width: 400,
                                    maxHeight: 120,
                                    overflow: "auto",
                                    border: 1,
                                    p: 0.25,
                                }}
                            >
                                {role.nonMembers.map((u) => (
                                    <ListItemButton
                                        key={u.guid}
                                        selected={selectedLeft[role.name] === u.guid}
                                        onClick={() => setSelectedLeft({ ...selectedLeft, [role.name]: u.guid })}
                                        sx={{ py: 0.25, px: 0.5, minHeight: 0 }}
                                    >
                                        <ListItemText
                                            primary={u.displayName}
                                            primaryTypographyProps={{
                                                fontFamily: "monospace",
                                                variant: "body2",
                                            }}
                                        />
                                    </ListItemButton>
                                ))}
                            </List>
                            <Stack spacing={1} justifyContent="center">
                                <IconButton onClick={() => void moveRight(role.name)}>
                                    <ArrowForwardIos />
                                </IconButton>
                                <IconButton onClick={() => void moveLeft(role.name)}>
                                    <ArrowBackIos />
                                </IconButton>
                            </Stack>
                            <List
                                sx={{
                                    width: 400,
                                    maxHeight: 120,
                                    overflow: "auto",
                                    border: 1,
                                    p: 0.25,
                                }}
                            >
                                {role.members.map((u) => (
                                    <ListItemButton
                                        key={u.guid}
                                        selected={selectedRight[role.name] === u.guid}
                                        onClick={() => setSelectedRight({ ...selectedRight, [role.name]: u.guid })}
                                        sx={{ py: 0.25, px: 0.5, minHeight: 0 }}
                                    >
                                        <ListItemText
                                            primary={u.displayName}
                                            primaryTypographyProps={{
                                                fontFamily: "monospace",
                                                variant: "body2",
                                            }}
                                        />
                                    </ListItemButton>
                                ))}
                            </List>
                        </Stack>
                    </Stack>
                ))}
            </Stack>
        </Box>
    );
};

export default AccountRolesPage;
