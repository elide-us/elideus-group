import { useEffect, useState } from 'react';
import { Table, TableHead, TableRow, TableCell, TableBody, Button, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { UserListItem, SystemUsersList1 } from './shared/RpcModels';
import { fetchList } from './rpc/system/users';

const AdminUsersPage = (): JSX.Element => {
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
        <>
            <Typography variant='h5' sx={{ mb: 2 }}>User Administration</Typography>
            <Table>
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
        </>
    );
};

export default AdminUsersPage;
