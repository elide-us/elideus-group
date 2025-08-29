import { useEffect, useState } from 'react';
import { Box, Table, TableHead, TableRow, TableCell, TableBody, Button } from '@mui/material';
import ColumnHeader from '../components/ColumnHeader';
import PageTitle from '../components/PageTitle';
import { Link as RouterLink } from 'react-router-dom';
import type { SupportRolesUserItem1, SupportRolesMembers1 } from '../shared/RpcModels';
import { fetchMembers } from '../rpc/support/roles';

const AccountUsersPage = (): JSX.Element => {
        const [users, setUsers] = useState<SupportRolesUserItem1[]>([]);

	useEffect(() => {
		void (async () => {
			try {
                                const res: SupportRolesMembers1 = await fetchMembers({ role: 'ROLE_REGISTERED' });
                                setUsers(res.members);
			} catch {
				setUsers([]);
			}
		})();
	}, []);

	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Account Users</PageTitle>
			<Table size="small" sx={{ '& td, & th': { py: 0.5 } }}>
				<TableHead>
					<TableRow>
						<ColumnHeader>Display Name</ColumnHeader>
						<ColumnHeader>Actions</ColumnHeader>
					</TableRow>
				</TableHead>
				<TableBody>
					{users.map((u) => (
						<TableRow key={u.guid}>
							<TableCell>{u.displayName}</TableCell>
							<TableCell>
								<Button component={RouterLink} to={`/account-users/${u.guid}`} variant="contained">Edit</Button>
							</TableCell>
						</TableRow>
					))}
				</TableBody>
			</Table>
		</Box>
	);
};

export default AccountUsersPage;
