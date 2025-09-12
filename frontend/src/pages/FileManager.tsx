import React, { useEffect, useState, useContext, useCallback } from 'react';
import {
    Box,
    Table,
    TableHead,
    TableRow,
    TableCell,
    TableBody,
    IconButton,
    Stack,
    Checkbox,
    FormControlLabel,
    Tooltip,
} from '@mui/material';
import {
    OpenInNew,
    Link as LinkIcon,
    Delete,
    Publish,
    DriveFileMove,
    Folder,
    Unpublished,
} from '@mui/icons-material';
import {
    fetchFolderFiles,
    fetchDeleteFiles,
    fetchSetGallery,
    fetchMoveFile,
    fetchDeleteFolder,
} from '../rpc/storage/files';
import PageTitle from '../components/PageTitle';
import ColumnHeader from '../components/ColumnHeader';
import Notification from '../components/Notification';
import UserContext from '../shared/UserContext';
import FileUpload from '../components/FileUpload';
import FolderManager from '../components/FolderManager';
import AudioPreview from '../components/AudioPreview';
import ImagePreview from '../components/ImagePreview';

interface StorageFile {
    path: string;
    name: string;
    url: string;
    content_type?: string;
    gallery?: boolean;
}

interface StorageFolder {
    name: string;
    empty: boolean;
}

const FileManager = (): JSX.Element => {
    const [files, setFiles] = useState<StorageFile[]>([]);
    const [folders, setFolders] = useState<StorageFolder[]>([]);
    const { userData } = useContext(UserContext);
    const [notification, setNotification] = useState(false);
    const [notificationMsg, setNotificationMsg] = useState('');
    const [currentPath, setCurrentPath] = useState('');
    const [moveTarget, setMoveTarget] = useState<string | null>(null);

    const load = useCallback(async (path: string): Promise<void> => {
        try {
            const res: { path: string; files: StorageFile[]; folders: StorageFolder[] } =
                await fetchFolderFiles({ path });
            const filtered = res.files.filter((f) => f.content_type !== 'path/folder');
            setFiles(filtered);
            setFolders(res.folders);
            setCurrentPath(res.path);
        } catch {
            setFiles([]);
            setFolders([]);
        }
    }, []);

    useEffect(() => {
        if (!userData) {
            setFiles([]);
            setFolders([]);
            return;
        }
        void load(currentPath);
    }, [userData, currentPath, load]);

    const getFullName = (file: StorageFile): string =>
        file.path ? `${file.path}/${file.name}` : file.name;

    const handleDelete = async (file: StorageFile): Promise<void> => {
        const name = getFullName(file);
        await fetchDeleteFiles({ files: [name] });
        await load(currentPath);
    };

    const handleDeleteFolder = async (folder: string): Promise<void> => {
        const path = currentPath ? `${currentPath}/${folder}` : folder;
        await fetchDeleteFolder({ path });
        await load(currentPath);
    };

    const handleSetGallery = async (file: StorageFile): Promise<void> => {
        await fetchSetGallery({ name: getFullName(file), gallery: !file.gallery });
        await load(currentPath);
    };

    const handleCopy = async (url: string): Promise<void> => {
        await navigator.clipboard.writeText(url);
        setNotificationMsg('Link copied');
        setNotification(true);
    };

    const handleMove = async (file: StorageFile): Promise<void> => {
        if (moveTarget === null) return;
        const src = getFullName(file);
        const base = file.name;
        const dst = moveTarget ? `${moveTarget}/${base}` : base;
        await fetchMoveFile({ src, dst });
        await load(currentPath);
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

    const renderPreview = (file: StorageFile): JSX.Element => {
        const type = getType(file);
        if (type === 'audio') {
            return <AudioPreview url={file.url} />;
        }
        if (type === 'image') {
            return <ImagePreview url={file.url} />;
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

    useEffect(() => {
        setMoveTarget(null);
    }, [currentPath]);
    const parentPath = currentPath.split('/').slice(0, -1).join('/');
    const displayFolders = currentPath ? [{ name: '..', empty: false }, ...folders] : folders;

    const navigateTo = (path: string): void => {
        setCurrentPath(path);
    };

    return (
        <Box sx={{ p: 2 }}>
            <Stack spacing={2}>
                <PageTitle>File Manager</PageTitle>
                <FileUpload onComplete={() => load(currentPath)} path={currentPath} />
                <FolderManager path={currentPath} onPathChange={navigateTo} onRefresh={() => load(currentPath)} />
                <Table size="small" sx={{ '& td, & th': { py: 0.5 } }}>
                    <TableHead>
                        <TableRow>
                            <ColumnHeader sx={{ width: '20%' }}>Preview</ColumnHeader>
                            <ColumnHeader sx={{ width: '60%' }}>Filename</ColumnHeader>
                            <ColumnHeader sx={{ width: '20%' }}>Actions</ColumnHeader>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {displayFolders.map((folder) => {
                            const fullPath =
                                folder.name === '..'
                                    ? parentPath
                                    : currentPath
                                      ? `${currentPath}/${folder.name}`
                                      : folder.name;
                            return (
                                <TableRow
                                    key={`folder-${folder.name}`}
                                    hover
                                    sx={{ cursor: 'pointer' }}
                                    onClick={() => navigateTo(fullPath)}
                                >
                                    <TableCell sx={{ width: '20%' }}>
                                        <IconButton size="small">
                                            <Folder />
                                        </IconButton>
                                    </TableCell>
                                    <TableCell sx={{ width: '60%' }}>{folder.name}</TableCell>
                                    <TableCell sx={{ width: '20%' }}>
                                        <Stack direction="row" spacing={1} alignItems="center">
                                            <FormControlLabel
                                                onClick={(e) => e.stopPropagation()}
                                                control={
                                                    <Checkbox
                                                        checked={moveTarget === fullPath}
                                                        disabled={moveTarget !== null && moveTarget !== fullPath}
                                                        onChange={(e) =>
                                                            setMoveTarget(
                                                                e.target.checked ? fullPath : null,
                                                            )
                                                        }
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                }
                                                label="Move to"
                                            />
                                            {folder.name !== '..' && (
                                                <IconButton
                                                    size="small"
                                                    disabled={!folder.empty}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        void handleDeleteFolder(folder.name);
                                                    }}
                                                >
                                                    <Delete />
                                                </IconButton>
                                            )}
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                        {files.map((file) => (
                            <TableRow key={file.name}>
                                <TableCell sx={{ width: '20%' }}>{renderPreview(file)}</TableCell>
                                <TableCell sx={{ width: '60%' }}>
                                    {file.name}
                                    {file.gallery && <Publish fontSize="small" sx={{ ml: 1 }} />}
                                </TableCell>
                                <TableCell sx={{ width: '20%' }}>
                                    <Stack direction="row" spacing={1}>
                                        <Tooltip title="Get link">
                                            <IconButton size="small" onClick={() => void handleCopy(file.url)}>
                                                <LinkIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Delete">
                                            <IconButton size="small" onClick={() => void handleDelete(file)}>
                                                <Delete />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title={file.gallery ? 'Unpublish' : 'Publish'}>
                                            <IconButton size="small" onClick={() => void handleSetGallery(file)}>
                                                {file.gallery ? <Unpublished /> : <Publish />}
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Move">
                                            <IconButton
                                                size="small"
                                                disabled={moveTarget === null}
                                                onClick={() => void handleMove(file)}
                                            >
                                                <DriveFileMove />
                                            </IconButton>
                                        </Tooltip>
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

