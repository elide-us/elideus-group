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
} from "../shared/RpcModels";
import {
    fetchRoles,
    fetchRoleMembers,
    fetchAddRoleMember,
    fetchRemoveRoleMember,
} from "../rpc/account/role";

const AccountRolesPage = (): JSX.Element => {
    const [roles, setRoles] = useState<string[]>([]);
    const [members, setMembers] = useState<Record<string, AccountRoleUserItem1[]>>({});
    const [nonMembers, setNonMembers] = useState<Record<string, AccountRoleUserItem1[]>>({});
    const [selectedLeft, setSelectedLeft] = useState<Record<string, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<string, string>>({});

    useEffect(() => {
        void (async () => {
            try {
                const res: AccountRoleList1 = await fetchRoles();
                setRoles(res.roles.map((r) => r.name).sort());
            } catch {
                setRoles([]);
            }
        })();
    }, []);

    useEffect(() => {
        roles.forEach((r) => {
            if (members[r]) return;
            void (async () => {
                try {
                    const res: AccountRoleMembers1 = await fetchRoleMembers({ role: r });
                    setMembers((m) => ({ ...m, [r]: res.members }));
                    setNonMembers((n) => ({ ...n, [r]: res.nonMembers }));
                } catch {
                    setMembers((m) => ({ ...m, [r]: [] }));
                    setNonMembers((n) => ({ ...n, [r]: [] }));
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
                    <Stack key={role} spacing={2} direction="column" alignItems="center">
                        <Typography variant="h6">{role}</Typography>
                        <Stack direction="row" spacing={2}>
                            <List sx={{ width: 200, border: 1 }}>
                                {(nonMembers[role] || []).map((u) => (
                                    <ListItemButton
                                        key={u.guid}
                                        selected={selectedLeft[role] === u.guid}
                                        onClick={() => setSelectedLeft({ ...selectedLeft, [role]: u.guid })}
                                    >
                                        <ListItemText primary={u.displayName} />
                                    </ListItemButton>
                                ))}
                            </List>
                            <Stack spacing={1} justifyContent="center">
                                <IconButton onClick={() => void moveRight(role)}>
                                    <ArrowForwardIos />
                                </IconButton>
                                <IconButton onClick={() => void moveLeft(role)}>
                                    <ArrowBackIos />
                                </IconButton>
                            </Stack>
                            <List sx={{ width: 200, border: 1 }}>
                                {(members[role] || []).map((u) => (
                                    <ListItemButton
                                        key={u.guid}
                                        selected={selectedRight[role] === u.guid}
                                        onClick={() => setSelectedRight({ ...selectedRight, [role]: u.guid })}
                                    >
                                        <ListItemText primary={u.displayName} />
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

