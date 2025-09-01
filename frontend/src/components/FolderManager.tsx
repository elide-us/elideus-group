import React, { useState } from 'react';
import { Box, IconButton, TextField, Button } from '@mui/material';
import { ArrowUpward } from '@mui/icons-material';
import { fetchCreateFolder } from '../rpc/storage/files';

interface FolderManagerProps {
    path: string;
    onPathChange: (path: string) => void;
    onRefresh?: () => Promise<void> | void;
}

const FolderManager = ({ path, onPathChange, onRefresh }: FolderManagerProps): JSX.Element => {
    const [newFolder, setNewFolder] = useState('');
    const isRoot = path === '';

    const handleUp = (): void => {
        if (isRoot) return;
        const parts = path.split('/');
        parts.pop();
        onPathChange(parts.join('/'));
    };

    const handleCreate = async (): Promise<void> => {
        const name = newFolder.trim();
        if (!name) return;
        const fullPath = path ? `${path}/${name}` : name;
        await fetchCreateFolder({ path: fullPath });
        setNewFolder('');
        if (onRefresh) await onRefresh();
    };

    return (
        <Box sx={{ border: '1px solid', borderColor: 'grey.500', p: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton size="small" onClick={handleUp} disabled={isRoot}>
                <ArrowUpward />
            </IconButton>
            <TextField value={`/${path}`} InputProps={{ readOnly: true }} sx={{ flexGrow: 1 }} />
            <TextField
                value={newFolder}
                onChange={(e) => setNewFolder(e.target.value)}
                placeholder="Folder name"
                sx={{ flexGrow: 1 }}
            />
            <Button onClick={() => void handleCreate()}>Create folder</Button>
        </Box>
    );
};

export default FolderManager;

