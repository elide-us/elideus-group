import React, { useEffect, useState, useContext } from 'react';
import {
    Box,
    Table,
    TableHead,
    TableRow,
    TableCell,
    TableBody,
    IconButton,
    Stack,
} from '@mui/material';
import {
    PlayArrow,
    OpenInNew,
    Link as LinkIcon,
    Delete,
    Publish,
    DriveFileMove,
    Folder,
} from '@mui/icons-material';
import {
    fetchFiles,
    fetchDeleteFiles,
    fetchSetGallery,
} from '../rpc/storage/files';
import PageTitle from '../components/PageTitle';
import ColumnHeader from '../components/ColumnHeader';
import Notification from '../components/Notification';
import UserContext from '../shared/UserContext';
import FileUpload from '../components/FileUpload';
import FolderManager from '../components/FolderManager';

interface StorageFile {
    name: string;
    url: string;
    content_type?: string;
}

const FileManager = (): JSX.Element => {
    const [files, setFiles] = useState<StorageFile[]>([]);
    const { userData } = useContext(UserContext);
    const [notification, setNotification] = useState(false);
    const [notificationMsg, setNotificationMsg] = useState('');
    const [currentPath, setCurrentPath] = useState('');

    const load = async (): Promise<void> => {
        try {
            const res: { files: StorageFile[] } = await fetchFiles();
            setFiles(res.files);
        } catch {
            setFiles([]);
        }
    };

    useEffect(() => {
        if (!userData) {
            setFiles([]);
            return;
        }
        void load();
    }, [userData]);


    const handleDelete = async (name: string): Promise<void> => {
        await fetchDeleteFiles({ files: [name] });
        await load();
    };

    const handleSetGallery = async (name: string): Promise<void> => {
        await fetchSetGallery({ name, gallery: true });
    };

    const handleCopy = async (url: string): Promise<void> => {
        await navigator.clipboard.writeText(url);
        setNotificationMsg('Link copied');
        setNotification(true);
    };

    const handleMove = (name: string): void => {
        console.log('move', name);
    };

    const getType = (file: StorageFile): string => {
        const type = file.content_type || '';
        if (type.startsWith('audio/')) return 'audio';
        if (type.startsWith('video/')) return 'video';
        if (type.startsWith('image/')) return 'image';
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        if (['mp3', 'wav', 'ogg'].includes(ext)) return 'audio';
        if (['mp4', 'webm'].includes(ext)) return 'video';
        if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext)) return 'image';
        return 'other';
    };

    const playAudio = (url: string): void => {
        const audio = new Audio(url);
        void audio.play();
    };

    const renderPreview = (file: StorageFile): JSX.Element => {
        const type = getType(file);
        if (type === 'audio') {
            return (
                <IconButton size="small" onClick={() => playAudio(file.url)}>
                    <PlayArrow />
                </IconButton>
            );
        }
        return (
            <IconButton size="small" onClick={() => window.open(file.url, '_blank')}>
                <OpenInNew />
            </IconButton>
        );
    };

    const handleNotificationClose = (): void => {
        setNotification(false);
    };

    const prefix = currentPath ? `${currentPath}/` : '';
    const folderSet = new Set<string>();
    const visibleFiles: StorageFile[] = [];
    files.forEach((file) => {
        if (!file.name.startsWith(prefix)) return;
        const rest = file.name.slice(prefix.length);
        const parts = rest.split('/');
        if (parts.length > 1) folderSet.add(parts[0]);
        else visibleFiles.push(file);
    });
    const folders = Array.from(folderSet);

    return (
        <Box sx={{ p: 2 }}>
            <Stack spacing={2}>
                <PageTitle>File Manager</PageTitle>
                <FileUpload onComplete={() => load()} path={currentPath} />
                <FolderManager path={currentPath} onPathChange={setCurrentPath} onRefresh={() => load()} />
                <Table size="small" sx={{ '& td, & th': { py: 0.5 } }}>
                    <TableHead>
                        <TableRow>
                            <ColumnHeader sx={{ width: '20%' }}>Preview</ColumnHeader>
                            <ColumnHeader sx={{ width: '60%' }}>Filename</ColumnHeader>
                            <ColumnHeader sx={{ width: '20%' }}>Actions</ColumnHeader>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {folders.map((folder) => (
                            <TableRow
                                key={`folder-${folder}`}
                                hover
                                sx={{ cursor: 'pointer' }}
                                onClick={() => setCurrentPath(prefix + folder)}
                            >
                                <TableCell sx={{ width: '20%' }}>
                                    <IconButton size="small">
                                        <Folder />
                                    </IconButton>
                                </TableCell>
                                <TableCell sx={{ width: '60%' }}>{folder}</TableCell>
                                <TableCell sx={{ width: '20%' }} />
                            </TableRow>
                        ))}
                        {visibleFiles.map((file) => (
                            <TableRow key={file.name}>
                                <TableCell sx={{ width: '20%' }}>{renderPreview(file)}</TableCell>
                                <TableCell sx={{ width: '60%' }}>{file.name}</TableCell>
                                <TableCell sx={{ width: '20%' }}>
                                    <Stack direction="row" spacing={1}>
                                        <IconButton size="small" onClick={() => void handleCopy(file.url)}>
                                            <LinkIcon />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => void handleDelete(file.name)}>
                                            <Delete />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => void handleSetGallery(file.name)}>
                                            <Publish />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => handleMove(file.name)}>
                                            <DriveFileMove />
                                        </IconButton>
                                    </Stack>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Stack>
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity="success"
                message={notificationMsg}
            />
        </Box>
    );
};

export default FileManager;

