import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import PageTitle from '../components/PageTitle';
import EditBox from '../components/EditBox';
import Notification from '../components/Notification';
import type {
    UsersProfileProfile1,
    SystemRolesRoleItem1 as ServiceRolesRoleItem1,
    SupportRolesMembers1,
} from '../shared/RpcModels';
import { fetchProfile, fetchSetCredits, fetchEnableStorage, fetchResetDisplay } from '../rpc/support/users';
import { fetchRoles as fetchServiceRoles } from '../rpc/service/roles';
import { fetchMembers, fetchAddMember, fetchRemoveMember } from '../rpc/support/roles';

const AccountUserPanel = (): JSX.Element => {
	const { guid } = useParams();
	const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
        const [roles, setRoles] = useState<ServiceRolesRoleItem1[]>([]);
	const [assigned, setAssigned] = useState<string[]>([]);
	const [available, setAvailable] = useState<string[]>([]);
	const [credits, setCredits] = useState<number>(0);
	const [notification, setNotification] = useState(false);
	const [initialAssigned, setInitialAssigned] = useState<string[]>([]);
	const [selectedLeft, setSelectedLeft] = useState('');
	const [selectedRight, setSelectedRight] = useState('');

	useEffect(() => {
		void (async () => {
			if (!guid) return;
			try {
				const prof: UsersProfileProfile1 = await fetchProfile({ userGuid: guid });
				setProfile(prof);
				setCredits(prof.credits);
                                const roleRes = await fetchServiceRoles();
                                const roleItems: ServiceRolesRoleItem1[] = roleRes.roles;
				setRoles(roleItems);
				const assignments: string[] = [];
				const avail: string[] = [];
				await Promise.all(
					roleItems.map(async (r) => {
						try {
							const members: SupportRolesMembers1 = await fetchMembers({ role: r.name });
							if (members.members.some((m) => m.guid === guid)) {
								assignments.push(r.name);
							} else {
								avail.push(r.name);
							}
						} catch {
							avail.push(r.name);
						}
					})
				);
				setAssigned(assignments);
				setAvailable(avail);
				setInitialAssigned(assignments);
			} catch {
				setProfile(null);
				setRoles([]);
				setAssigned([]);
				setAvailable([]);
				setInitialAssigned([]);
			}
		})();
	}, [guid]);

	const moveRight = (): void => {
		if (!selectedLeft) return;
		setAssigned([...assigned, selectedLeft]);
		setAvailable(available.filter((r) => r !== selectedLeft));
		setSelectedLeft('');
	};

	const moveLeft = (): void => {
		if (!selectedRight) return;
		setAvailable([...available, selectedRight]);
		setAssigned(assigned.filter((r) => r !== selectedRight));
		setSelectedRight('');
	};

	const handleResetDisplay = async (): Promise<void> => {
		if (!guid) return;
		await fetchResetDisplay({ userGuid: guid });
		const prof: UsersProfileProfile1 = await fetchProfile({ userGuid: guid });
		setProfile(prof);
	};

	const handleEnableStorage = async (): Promise<void> => {
		if (!guid) return;
		await fetchEnableStorage({ userGuid: guid });
	};

	const handleSave = async (): Promise<void> => {
		if (!guid) return;
		const toAdd = assigned.filter((r) => !initialAssigned.includes(r));
		const toRemove = initialAssigned.filter((r) => !assigned.includes(r));
		await Promise.all(toAdd.map((r) => fetchAddMember({ role: r, userGuid: guid })));
		await Promise.all(toRemove.map((r) => fetchRemoveMember({ role: r, userGuid: guid })));
		await fetchSetCredits({ userGuid: guid, credits });
		setInitialAssigned(assigned);
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
					<Button variant="outlined" onClick={handleEnableStorage}>Enable Storage</Button>
				</Stack>
			)}
			<Stack direction="row" spacing={2}>
				<List sx={{ width: 200, border: 1 }}>
					{available.map((r) => (
						<ListItemButton key={r} selected={selectedLeft === r} onClick={() => setSelectedLeft(r)}>
							<ListItemText primary={roles.find((ro) => ro.name === r)?.display ?? r} />
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
						<ListItemButton key={r} selected={selectedRight === r} onClick={() => setSelectedRight(r)}>
							<ListItemText primary={roles.find((ro) => ro.name === r)?.display ?? r} />
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
