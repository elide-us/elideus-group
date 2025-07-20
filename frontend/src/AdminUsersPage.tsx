import { useEffect, useState } from 'react';
import { Table, TableHead, TableRow, TableCell, TableBody, Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { UserListItem, AdminUsersList1 } from './shared/RpcModels';
import { fetchList } from './rpc/admin/users';

const AdminUsersPage = (): JSX.Element => {
    const [users, setUsers] = useState<UserListItem[]>([]);

    useEffect(() => {
        void (async () => {
            try {
                const res: AdminUsersList1 = await fetchList();
                setUsers(res.users);
            } catch {
                setUsers([]);
            }
        })();
    }, []);

    return (
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
                            <Button component={RouterLink} to={`/admin_userpanel/${u.guid}`} variant='contained'>Edit</Button>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};

export default AdminUsersPage;
