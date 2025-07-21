import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography, Avatar, TextField } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import type { AdminUserRoles1, AdminUserProfile1 } from './shared/RpcModels';
import { fetchRoles, fetchSetRoles, fetchListRoles, fetchProfile } from './rpc/admin/users';

const AdminUserPanel = (): JSX.Element => {
    const { guid } = useParams();
    const [assigned, setAssigned] = useState<string[]>([]);
    const [available, setAvailable] = useState<string[]>([]);
    const [profile, setProfile] = useState<AdminUserProfile1 | null>(null);
    const [selectedLeft, setSelectedLeft] = useState<string | null>(null);
    const [selectedRight, setSelectedRight] = useState<string | null>(null);

    useEffect(() => {
        void (async () => {
            if (!guid) return;
            try {
                const roles: AdminUserRoles1 = await fetchRoles({ userGuid: guid });
                const all: AdminUserRoles1 = await fetchListRoles();
                const prof: AdminUserProfile1 = await fetchProfile({ userGuid: guid });
                setProfile(prof);
                setAssigned(roles.roles);
                setAvailable(all.roles.filter(r => !roles.roles.includes(r)));
            } catch {
                setAssigned([]);
                setAvailable([]);
                setProfile(null);
            }
        })();
    }, [guid]);

    const moveRight = (): void => {
        if (!selectedLeft) return;
        setAssigned([...assigned, selectedLeft]);
        setAvailable(available.filter(r => r !== selectedLeft));
        setSelectedLeft(null);
    };

    const moveLeft = (): void => {
        if (!selectedRight) return;
        setAvailable([...available, selectedRight]);
        setAssigned(assigned.filter(r => r !== selectedRight));
        setSelectedRight(null);
    };

    const handleSave = async (): Promise<void> => {
        if (!guid) return;
        await fetchSetRoles({ userGuid: guid, roles: assigned });
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Stack spacing={2} alignItems='center'>
                <Typography variant='h5'>Admin User Panel</Typography>
                {profile && (
                    <Stack spacing={1} alignItems='center'>
                        <Avatar src={undefined} sx={{ width: 80, height: 80 }} />
                        <TextField label='Display Name' value={profile.displayName} InputProps={{ readOnly: true }} fullWidth />
                        <Typography>Email: {profile.email}</Typography>
                        <Typography>Credits: {profile.credits ?? 0}</Typography>
                        <Typography>Storage Used: {profile.storageUsed ?? 0} MB</Typography>
                    </Stack>
                )}
                <Typography variant='h6'>Security Roles</Typography>
                <Stack direction='row' spacing={2}>
                    <List sx={{ width: 200, border: 1 }}>
                        {available.map((r) => (
                            <ListItemButton key={r} selected={selectedLeft === r} onClick={() => setSelectedLeft(r)}>
                                <ListItemText primary={r} />
                            </ListItemButton>
                        ))}
                    </List>
                    <Stack spacing={1} justifyContent='center'>
                        <IconButton onClick={moveRight}><ArrowForwardIos /></IconButton>
                        <IconButton onClick={moveLeft}><ArrowBackIos /></IconButton>
                    </Stack>
                    <List sx={{ width: 200, border: 1 }}>
                        {assigned.map((r) => (
                            <ListItemButton key={r} selected={selectedRight === r} onClick={() => setSelectedRight(r)}>
                                <ListItemText primary={r} />
                            </ListItemButton>
                        ))}
                    </List>
                </Stack>
                <Button variant='contained' onClick={handleSave}>Save</Button>
            </Stack>
        </Box>
    );
};

export default AdminUserPanel;
