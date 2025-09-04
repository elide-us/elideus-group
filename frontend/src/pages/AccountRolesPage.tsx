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
    AccountRoleUserItem1,
    AccountRoleMembers1,
    AccountRoleList1,
    AccountRoleRoleItem1,
} from "../shared/RpcModels";
import {
    fetchRoles,
    fetchRoleMembers,
    fetchAddRoleMember,
    fetchRemoveRoleMember,
} from "../rpc/account/role";

const AccountRolesPage = (): JSX.Element => {
    const [roles, setRoles] = useState<AccountRoleRoleItem1[]>([]);
    const [members, setMembers] = useState<Record<string, AccountRoleUserItem1[]>>({});
    const [nonMembers, setNonMembers] = useState<Record<string, AccountRoleUserItem1[]>>({});
    const [selectedLeft, setSelectedLeft] = useState<Record<string, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<string, string>>({});

    useEffect(() => {
        void (async () => {
            try {
                const res: AccountRoleList1 = await fetchRoles();
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
        })();
    }, []);

    useEffect(() => {
        roles.forEach((r) => {
            const name = r.name;
            if (members[name]) return;
            void (async () => {
                try {
                    const res: AccountRoleMembers1 = await fetchRoleMembers({ role: name });
                    setMembers((m) => ({ ...m, [name]: res.members }));
                    setNonMembers((n) => ({ ...n, [name]: res.nonMembers }));
                } catch {
                    setMembers((m) => ({ ...m, [name]: [] }));
                    setNonMembers((n) => ({ ...n, [name]: [] }));
                }
            })();
        });
    }, [roles, members]);

    const moveRight = async (role: string): Promise<void> => {
        const id = selectedLeft[role];
        if (!id) return;
        await fetchAddRoleMember({ role, userGuid: id });
        const res: AccountRoleMembers1 = await fetchRoleMembers({ role });
        setMembers((m) => ({ ...m, [role]: res.members }));
        setNonMembers((n) => ({ ...n, [role]: res.nonMembers }));
        setSelectedLeft((s) => ({ ...s, [role]: "" }));
    };

    const moveLeft = async (role: string): Promise<void> => {
        const id = selectedRight[role];
        if (!id) return;
        await fetchRemoveRoleMember({ role, userGuid: id });
        const res: AccountRoleMembers1 = await fetchRoleMembers({ role });
        setMembers((m) => ({ ...m, [role]: res.members }));
        setNonMembers((n) => ({ ...n, [role]: res.nonMembers }));
        setSelectedRight((s) => ({ ...s, [role]: "" }));
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
                                {(nonMembers[role.name] || []).map((u) => (
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
                                {(members[role.name] || []).map((u) => (
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

