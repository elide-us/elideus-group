import React, { useEffect, useState, useContext } from 'react';
import {
	Box,
	Button,
	List,
	ListItem,
	ListItemText,
	Stack,
} from '@mui/material';
import {
        fetchFiles,
        fetchUploadFiles,
        fetchDeleteFiles,
        fetchSetGallery,
} from '../rpc/storage/files';
import PageTitle from '../components/PageTitle';
import UserContext from '../shared/UserContext';

interface StorageFile {
	name: string;
	url: string;
	content_type?: string;
}

const FileManager = (): JSX.Element => {
        const [files, setFiles] = useState<StorageFile[]>([]);
        const { userData } = useContext(UserContext);

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

	const fileToUpload = (file: File): Promise<{ name: string; content_b64: string; content_type?: string }> => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => {
				const result = reader.result as string;
				const content_b64 = result.split(',')[1] ?? '';
				resolve({ name: file.name, content_b64, content_type: file.type || undefined });
			};
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	};

	const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
		const selected = e.target.files;
		if (!selected || selected.length === 0) return;
		const uploads = await Promise.all(Array.from(selected).map(fileToUpload));
		await fetchUploadFiles({ files: uploads });
		e.target.value = '';
		await load();
	};

	const handleDelete = async (name: string): Promise<void> => {
		await fetchDeleteFiles({ files: [name] });
		await load();
	};

	const handleSetGallery = async (name: string): Promise<void> => {
		await fetchSetGallery({ name, gallery: true });
	};

	return (
		<Box>
			<PageTitle>File Manager</PageTitle>
			<input type="file" multiple onChange={handleUpload} />
			<List>
				{files.map((file) => (
					<ListItem key={file.name}>
						<ListItemText primary={file.name} />
						<Stack direction="row" spacing={1}>
							<Button variant="contained" size="small" onClick={() => handleSetGallery(file.name)}>
								Set Gallery
							</Button>
							<Button variant="outlined" color="error" size="small" onClick={() => handleDelete(file.name)}>
								Delete
							</Button>
						</Stack>
					</ListItem>
				))}
			</List>
		</Box>
	);
};

export default FileManager;

