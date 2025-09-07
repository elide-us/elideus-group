import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import PageTitle from '../components/PageTitle';
import EditBox from '../components/EditBox';
import Notification from '../components/Notification';
import type {
    UsersProfileProfile1,
    AccountRoleRoleItem1,
    AccountRoleMembers1,
    AccountRoleList1,
} from '../shared/RpcModels';
import {
    fetchProfile,
    fetchSetCredits,
    fetchResetDisplay,
    fetchEnableStorage,
    fetchCheckStorage,
} from '../rpc/account/user';
import {
    fetchRoles,
    fetchRoleMembers,
    fetchAddRoleMember,
    fetchRemoveRoleMember,
} from '../rpc/account/role';

const STORAGE_ROLE_BIT = 2n;

const AccountUserPanel = (): JSX.Element => {
        const { guid } = useParams();
        const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
        const [assigned, setAssigned] = useState<AccountRoleRoleItem1[]>([]);
        const [available, setAvailable] = useState<AccountRoleRoleItem1[]>([]);
        const [credits, setCredits] = useState<number>(0);
        const [notification, setNotification] = useState(false);
        const [initialAssigned, setInitialAssigned] = useState<string[]>([]);
        const [selectedLeft, setSelectedLeft] = useState('');
        const [selectedRight, setSelectedRight] = useState('');
        const [storageExists, setStorageExists] = useState(false);

        const sortRoles = (a: AccountRoleRoleItem1, b: AccountRoleRoleItem1): number => {
                const am = BigInt(a.mask);
                const bm = BigInt(b.mask);
                if (am < bm) return -1;
                if (am > bm) return 1;
                return 0;
        };

        useEffect(() => {
                void (async () => {
                        if (!guid) return;
                        try {
                                const prof: UsersProfileProfile1 = await fetchProfile({ userGuid: guid });
                                setProfile(prof);
                                setCredits(prof.credits);
                                const roleRes: AccountRoleList1 = await fetchRoles();
                                const sorted = [...roleRes.roles].sort(sortRoles);
                                const assignments: AccountRoleRoleItem1[] = [];
                                const avail: AccountRoleRoleItem1[] = [];
                                await Promise.all(
                                        sorted.map(async (r) => {
                                                try {
                                                        const members: AccountRoleMembers1 = await fetchRoleMembers({ role: r.name });
                                                        if (members.members.some((m) => m.guid === guid)) {
                                                                assignments.push(r);
                                                        } else {
                                                                avail.push(r);
                                                        }
                                                } catch {
                                                        avail.push(r);
                                                }
                                        })
                                );
                                assignments.sort(sortRoles);
                                avail.sort(sortRoles);
                                setAssigned(assignments);
                                setAvailable(avail);
                                setInitialAssigned(assignments.map((r) => r.name));
                        } catch {
                                setProfile(null);
                                setAssigned([]);
                                setAvailable([]);
                                setInitialAssigned([]);
                        }
                })();
        }, [guid]);

        useEffect(() => {
                if (!profile) return;
                const hasStorage = assigned.some((r) => (BigInt(r.mask) & STORAGE_ROLE_BIT) !== 0n);
                if (hasStorage) {
                        void (async () => {
                                try {
                                        const res = await fetchCheckStorage({ userGuid: profile.guid });
                                        setStorageExists(Boolean(res.exists));
                                } catch {
                                        setStorageExists(false);
                                }
                        })();
                } else {
                        setStorageExists(false);
                }
        }, [assigned, profile]);

        const moveRight = (): void => {
                if (!selectedLeft) return;
                const role = available.find((r) => r.name === selectedLeft);
                if (!role) return;
                setAssigned([...assigned, role].sort(sortRoles));
                setAvailable(available.filter((r) => r.name !== selectedLeft));
                setSelectedLeft('');
        };

        const moveLeft = (): void => {
                if (!selectedRight) return;
                const role = assigned.find((r) => r.name === selectedRight);
                if (!role) return;
                setAvailable([...available, role].sort(sortRoles));
                setAssigned(assigned.filter((r) => r.name !== selectedRight));
                setSelectedRight('');
        };

        const handleResetDisplay = async (): Promise<void> => {
                if (!profile) return;
                await fetchResetDisplay({ userGuid: profile.guid });
                const prof: UsersProfileProfile1 = await fetchProfile({ userGuid: profile.guid });
                setProfile(prof);
        };

        const handleEnableStorage = async (): Promise<void> => {
                if (!profile) return;
                await fetchEnableStorage({ userGuid: profile.guid });
                const res = await fetchCheckStorage({ userGuid: profile.guid });
                setStorageExists(Boolean(res.exists));
        };

        const handleSave = async (): Promise<void> => {
                if (!profile) return;
                const assignedNames = assigned.map((r) => r.name);
                const toAdd = assignedNames.filter((r) => !initialAssigned.includes(r));
                const toRemove = initialAssigned.filter((r) => !assignedNames.includes(r));
                await Promise.all(toAdd.map((r) => fetchAddRoleMember({ role: r, userGuid: profile.guid })));
                await Promise.all(toRemove.map((r) => fetchRemoveRoleMember({ role: r, userGuid: profile.guid })));
                await fetchSetCredits({ userGuid: profile.guid, credits });
                setInitialAssigned(assignedNames);
                setNotification(true);
        };

	return (
		<Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
			<PageTitle>User Management</PageTitle>
			{profile && (
				<Stack spacing={2} sx={{ mb: 4, alignItems: 'center' }}>
					<Typography variant="h6">{profile.display_name}</Typography>
					<Button variant="outlined" onClick={handleResetDisplay}>Reset Display Name</Button>
					<Typography>Email: {profile.email}</Typography>
					<EditBox value={credits} onCommit={(val) => setCredits(Number(val))} width={120} />
                                        <Button variant="outlined" onClick={handleEnableStorage} disabled={!assigned.some((r) => (BigInt(r.mask) & STORAGE_ROLE_BIT) !== 0n) || storageExists}>Enable Storage</Button>
                                </Stack>
                        )}
			<Stack direction="row" spacing={2}>
				<List sx={{ width: 200, border: 1 }}>
					{available.map((r) => (
						<ListItemButton key={r.name} selected={selectedLeft === r.name} onClick={() => setSelectedLeft(r.name)}>
							<ListItemText primary={r.display ?? r.name} />
						</ListItemButton>
					))}
				</List>
				<Stack spacing={1} justifyContent="center">
					<IconButton onClick={moveRight}>
						<ArrowForwardIos />
					</IconButton>
					<IconButton onClick={moveLeft}>
						<ArrowBackIos />
					</IconButton>
				</Stack>
				<List sx={{ width: 200, border: 1 }}>
					{assigned.map((r) => (
						<ListItemButton key={r.name} selected={selectedRight === r.name} onClick={() => setSelectedRight(r.name)}>
							<ListItemText primary={r.display ?? r.name} />
						</ListItemButton>
					))}
				</List>
			</Stack>
			<Box sx={{ mt: 2 }}>
				<Button variant="contained" onClick={handleSave}>Save</Button>
			</Box>
			<Notification open={notification} handleClose={() => setNotification(false)} severity="success" message="Saved" />
		</Box>
	);
};

export default AccountUserPanel;
