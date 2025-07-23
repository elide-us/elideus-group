import { useEffect, useState } from 'react';
import { Box, Divider, Table, TableHead, TableRow, TableCell, TableBody, Button, Typography } from '@mui/material';
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
            <Typography variant='h5'>User Accounts</Typography>
            <Divider sx={{ mb: 2 }} />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <TableCell>Display Name</TableCell>
                        <TableCell>Actions</TableCell>
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
