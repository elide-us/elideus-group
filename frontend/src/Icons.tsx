import { Box, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';
import { iconMap } from './icons';

const Icons = (): JSX.Element => {
    return (
        <Box sx={{ mt: 2 }}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Icon</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Alias</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {Object.entries(iconMap).map(([alias, IconComp]) => (
                        <TableRow key={alias}>
                            <TableCell><IconComp /></TableCell>
                            <TableCell>{alias.charAt(0).toUpperCase() + alias.slice(1) + 'Icon'}</TableCell>
                            <TableCell>{alias}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Box>
    );
};

export default Icons;
