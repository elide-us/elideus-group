import { TableCell, Typography } from '@mui/material';

const ColumnHeader = ({ title }: { title: string }): JSX.Element => (
    <TableCell>
        <Typography variant='columnHeader'>{title}</Typography>
    </TableCell>
);

export default ColumnHeader;
