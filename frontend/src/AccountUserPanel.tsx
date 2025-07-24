import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Divider, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography, Avatar, TextField } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos, CheckCircle, Cancel } from '@mui/icons-material';
import type { AccountUserRoles1, AccountUserProfile1, RoleItem } from './shared/RpcModels';
import { fetchRoles, fetchSetRoles, fetchProfile, fetchSetCredits, fetchEnableStorage, fetchSetDisplayName } from './rpc/account/users';
import { fetchList as fetchRoleList } from './rpc/account/roles';

const AccountUserPanel = (): JSX.Element => {
    const { guid } = useParams();
    const [assigned, setAssigned] = useState<string[]>([]);
    const [available, setAvailable] = useState<string[]>([]);
    const [profile, setProfile] = useState<AccountUserProfile1 | null>(null);
    const [username, setUsername] = useState<string>('');
    const [roles, setRoles] = useState<RoleItem[]>([]);
    const [credits, setCredits] = useState<number>(0);
    const [storageEnabled, setStorageEnabled] = useState<boolean>(false);
    const [storageUsed, setStorageUsed] = useState<number>(0);
    const [selectedLeft, setSelectedLeft] = useState<string | null>(null);
    const [selectedRight, setSelectedRight] = useState<string | null>(null);

    useEffect(() => {
        void (async () => {
            if (!guid) return;
            try {
                const userRoles: AccountUserRoles1 = await fetchRoles({ userGuid: guid });
                const roleList = await fetchRoleList();
                const prof: AccountUserProfile1 = await fetchProfile({ userGuid: guid });
                setRoles(roleList.roles);
                setAssigned(userRoles.roles);
                setAvailable(roleList.roles.map(r => r.name).filter(r => !userRoles.roles.includes(r)));
                setProfile(prof);
                setUsername(prof.username);
                setCredits(prof.credits ?? 0);
                setStorageEnabled(prof.storageEnabled ?? false);
                setStorageUsed(prof.storageUsed ?? 0);
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

    const handleEnableStorage = async (): Promise<void> => {
        if (!guid) return;
        const prof = await fetchEnableStorage({ userGuid: guid });
        setProfile(prof);
        setStorageEnabled(prof.storageEnabled ?? false);
        setStorageUsed(prof.storageUsed ?? 0);
    };

    const handleNameCommit = async (): Promise<void> => {
        if (!guid || !profile) return;
        if (username === profile.username) return;
        const updated = await fetchSetDisplayName({ userGuid: guid, displayName: username });
        setProfile(updated);
    };

    const handleSave = async (): Promise<void> => {
        if (!guid) return;
        await fetchSetRoles({ userGuid: guid, roles: assigned });
        await fetchSetCredits({ userGuid: guid, credits });
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 2, p: 2 }}>
            <Typography variant='h5'>User Management</Typography>
            <Divider sx={{ mb: 2 }} />
            {profile && (
                <Stack spacing={2} sx={{ mb: 4, alignItems: 'center' }}>
                    <Typography variant='h5'>User Profile</Typography>
                    <Avatar
                        src={profile.profilePicture ? `data:image/png;base64,${profile.profilePicture}` : undefined}
                        sx={{ width: 80, height: 80 }}
                    />
                    <TextField
                        label='Display Name'
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        onBlur={() => void handleNameCommit()}
                        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void handleNameCommit(); } }}
                    />
                    <Typography>Email: {profile.email}</Typography>
                    <TextField label='Credits' type='number' value={credits} onChange={e => setCredits(Number(e.target.value))} />
                    <Stack direction='row' spacing={1} alignItems='center'>
                        <Typography>Storage Enabled:</Typography>
                        {storageEnabled ? <CheckCircle color='success' /> : <IconButton onClick={handleEnableStorage}><Cancel color='error' /></IconButton>}
                    </Stack>
                    <Typography>Storage Used: {storageUsed} B</Typography>
                </Stack>
            )}
            <Stack direction='row' spacing={2}>
                <List sx={{ width: 200, border: 1 }}>
                    {available.map((r) => (
                        <ListItemButton key={r} selected={selectedLeft === r} onClick={() => setSelectedLeft(r)}>
                            <ListItemText primary={roles.find(ro => ro.name === r)?.display ?? r} />
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
                            <ListItemText primary={roles.find(ro => ro.name === r)?.display ?? r} />
                        </ListItemButton>
                    ))}
                </List>
            </Stack>
            <Box sx={{ ml: 2 }}>
                <Button variant='contained' onClick={handleSave}>Save</Button>
            </Box>
        </Box>
    );
};

export default AccountUserPanel;
