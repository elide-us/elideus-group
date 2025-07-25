import { useEffect, useState } from 'react';
import { Box, Table, TableHead, TableRow, TableCell, TableBody, Button } from '@mui/material';
import ColumnHeader from './shared/ColumnHeader';
import { PageTitle } from './shared/PageTitle';
import { Link as RouterLink } from 'react-router-dom';
import type { UserListItem, SystemUsersList1 } from './shared/RpcModels';
import { fetchList } from './rpc/system/users';

const AccountUsersPage = (): JSX.Element => {
    const [users, setUsers] = useState<UserListItem[]>([]);

    useEffect(() => {
        void (async () => {
            try {
                const res: SystemUsersList1 = await fetchList();
                setUsers(res.users);
            } catch {
                setUsers([]);
            }
        })();
    }, []);

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='User Accounts' />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <ColumnHeader title='Display Name' />
                        <ColumnHeader title='Actions' />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {users.map((u) => (
                        <TableRow key={u.guid}>
                            <TableCell>{u.displayName}</TableCell>
                            <TableCell>
                                <Button component={RouterLink} to={`/account_userpanel/${u.guid}`} variant='contained'>Edit</Button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Box>
    );
};

export default AccountUsersPage;
