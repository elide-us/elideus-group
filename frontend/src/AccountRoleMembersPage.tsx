import { useEffect, useState } from 'react';
import { Box, Stack, List, ListItemButton, ListItemText, IconButton, Typography } from '@mui/material';
import { PageTitle } from './shared/PageTitle';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import type { RoleItem, AccountRoleMembers2, UserListItem, AccountRolesList2 } from './shared/RpcModels';
import { fetchList2 as fetchList, fetchMembers2 as fetchMembers, fetchAddMember2 as fetchAddMember, fetchRemoveMember2 as fetchRemoveMember } from './rpc/account/roles';

const AccountRoleMembersPage = (): JSX.Element => {
    const [roles, setRoles] = useState<RoleItem[]>([]);
    const [members, setMembers] = useState<Record<string, UserListItem[]>>({});
    const [nonMembers, setNonMembers] = useState<Record<string, UserListItem[]>>({});
    const [selectedLeft, setSelectedLeft] = useState<Record<string, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<string, string>>({});

    useEffect(() => {
        void (async () => {
            try {
                const res: AccountRolesList2 = await fetchList();
                setRoles(res.roles.sort((a, b) => a.bit - b.bit));
            } catch {
                setRoles([]);
            }
        })();
    }, []);

    useEffect(() => {
        roles.forEach(r => {
            if (members[r.name]) return;
            void (async () => {
                try {
                    const res: AccountRoleMembers2 = await fetchMembers({ role: r.name });
                    setMembers(m => ({ ...m, [r.name]: res.members }));
                    setNonMembers(n => ({ ...n, [r.name]: res.nonMembers }));
                } catch {
                    setMembers(m => ({ ...m, [r.name]: [] }));
                    setNonMembers(n => ({ ...n, [r.name]: [] }));
                }
            })();
        });
    }, [roles, members]);

    const moveRight = async (role: string): Promise<void> => {
        const id = selectedLeft[role];
        if (!id) return;
        await fetchAddMember({ role, userGuid: id });
        const res: AccountRoleMembers2 = await fetchMembers({ role });
        setMembers(m => ({ ...m, [role]: res.members }));
        setNonMembers(n => ({ ...n, [role]: res.nonMembers }));
        setSelectedLeft(s => ({ ...s, [role]: '' }));
    };

    const moveLeft = async (role: string): Promise<void> => {
        const id = selectedRight[role];
        if (!id) return;
        await fetchRemoveMember({ role, userGuid: id });
        const res: AccountRoleMembers2 = await fetchMembers({ role });
        setMembers(m => ({ ...m, [role]: res.members }));
        setNonMembers(n => ({ ...n, [role]: res.nonMembers }));
        setSelectedRight(s => ({ ...s, [role]: '' }));
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='Role Memberships' />
            <Stack spacing={2}>
            {roles.map((role) => (
                <Stack key={role.name} spacing={2} direction='column' alignItems='center'>
                    <Typography variant='h6'>{role.display}</Typography>
                    <Stack direction='row' spacing={2}>
                        <List sx={{ width: 200, border: 1 }}>
                            {(nonMembers[role.name] || []).map(u => (
                                <ListItemButton key={u.guid} selected={selectedLeft[role.name] === u.guid} onClick={() => setSelectedLeft({ ...selectedLeft, [role.name]: u.guid })}>
                                    <ListItemText primary={u.displayName} />
                                </ListItemButton>
                            ))}
                        </List>
                        <Stack spacing={1} justifyContent='center'>
                            <IconButton onClick={() => void moveRight(role.name)}><ArrowForwardIos /></IconButton>
                            <IconButton onClick={() => void moveLeft(role.name)}><ArrowBackIos /></IconButton>
                        </Stack>
                        <List sx={{ width: 200, border: 1 }}>
                            {(members[role.name] || []).map(u => (
                                <ListItemButton key={u.guid} selected={selectedRight[role.name] === u.guid} onClick={() => setSelectedRight({ ...selectedRight, [role.name]: u.guid })}>
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

export default AccountRoleMembersPage;
