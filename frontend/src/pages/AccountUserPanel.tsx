import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import PageTitle from '../components/PageTitle';
import EditBox from '../components/EditBox';
import Notification from '../components/Notification';
import type {
        AccountRoleRoleItem1,
        AccountRoleMembers1,
        AccountRoleList1,
        AccountUserDisplayName1,
        AccountUserCredits1,
} from '../shared/RpcModels';
import {
        fetchDisplayname,
        fetchCredits,
        fetchSetCredits,
        fetchResetDisplay,
} from '../rpc/account/user';
import {
	fetchRoles,
	fetchRoleMembers,
	fetchAddRoleMember,
	fetchRemoveRoleMember,
} from '../rpc/account/role';

const AccountUserPanel = (): JSX.Element => {
                const { guid } = useParams();
                const [displayName, setDisplayName] = useState<string>('');
                const [assigned, setAssigned] = useState<AccountRoleRoleItem1[]>([]);
                const [available, setAvailable] = useState<AccountRoleRoleItem1[]>([]);
                const [credits, setCredits] = useState<number>(0);
                const [notification, setNotification] = useState(false);
                const [initialAssigned, setInitialAssigned] = useState<string[]>([]);
                const [selectedLeft, setSelectedLeft] = useState('');
                const [selectedRight, setSelectedRight] = useState('');

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
                                                                const nameRes: AccountUserDisplayName1 = await fetchDisplayname({ userGuid: guid });
                                                                setDisplayName(nameRes.displayName);
                                                                const creditRes: AccountUserCredits1 = await fetchCredits({ userGuid: guid });
                                                                setCredits(creditRes.credits);
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
                                                                setDisplayName('');
                                                                setCredits(0);
                                                                setAssigned([]);
                                                                setAvailable([]);
                                                                setInitialAssigned([]);
                                                }
                                })();
                }, [guid]);

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
                                if (!guid) return;
                                await fetchResetDisplay({ userGuid: guid });
                                const nameRes: AccountUserDisplayName1 = await fetchDisplayname({ userGuid: guid });
                                setDisplayName(nameRes.displayName);
                };

                const handleSave = async (): Promise<void> => {
                                if (!guid) return;
                                const assignedNames = assigned.map((r) => r.name);
                                const toAdd = assignedNames.filter((r) => !initialAssigned.includes(r));
                                const toRemove = initialAssigned.filter((r) => !assignedNames.includes(r));
                                await Promise.all(toAdd.map((r) => fetchAddRoleMember({ role: r, userGuid: guid })));
                                await Promise.all(toRemove.map((r) => fetchRemoveRoleMember({ role: r, userGuid: guid })));
                                setInitialAssigned(assignedNames);
                                setNotification(true);
                };

	return (
		<Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
			<PageTitle>User Management</PageTitle>
                        {displayName && (
                                <Stack spacing={2} sx={{ mb: 4, alignItems: 'center' }}>
                                        <Typography variant="h6">{displayName}</Typography>
                                        <Button variant="outlined" onClick={handleResetDisplay}>Reset Display Name</Button>
                                        <EditBox
                                                value={credits}
                                                onCommit={async (val) => {
                                                                if (!guid) return;
                                                                const num = Number(val);
                                                                await fetchSetCredits({ userGuid: guid, credits: num });
                                                                setCredits(num);
                                                }}
                                                width={120}
                                        />
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
