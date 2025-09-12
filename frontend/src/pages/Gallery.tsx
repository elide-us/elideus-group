import { useState, useEffect, type JSX } from 'react';
import { Tabs, Tab, Stack } from '@mui/material';
import PageTitle from '../components/PageTitle';
import Postcard from '../components/Postcard';
import { fetchPublicFiles } from '../rpc/public/gallery';
import { fetchReportFile } from '../rpc/storage/files';

const Gallery = (): JSX.Element => {
	    const [value, setValue] = useState(0);
	    const [files, setFiles] = useState<any[]>([]);

	    useEffect(() => {
	            void (async () => {
	                    try {
	                            const res = await fetchPublicFiles();
	                            setFiles((res as any).files ?? []);
	                    } catch {
	                            setFiles([]);
	                    }
	            })();
	    }, []);

	    const handleReport = (guid: string, name: string): void => {
	            void fetchReportFile({ guid, name });
	    };

	    const getType = (ct: string | undefined): number => {
	            if (!ct) return 4;
	            if (ct.startsWith('image/')) return 0;
	            if (ct.startsWith('video/')) return 1;
	            if (ct.startsWith('audio/')) return 2;
	            if (ct.startsWith('application/') || ct.startsWith('text/')) return 3;
	            return 4;
	    };

	    return (
	            <div>
	                    <PageTitle>Gallery</PageTitle>
	                    <Tabs
	                            value={value}
	                            onChange={(_e, newValue) => setValue(newValue)}
	                            aria-label="gallery filters"
	                    >
	                            <Tab label="Image" />
	                            <Tab label="Video" />
	                            <Tab label="Audio" />
	                            <Tab label="Document" />
	                            <Tab label="Misc" />
	                    </Tabs>
	                    <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ mt: 2 }}>
                                    {files.filter((f) => getType(f.content_type) === value).map((f, idx) => {
                                            const name = f.path ? `${f.path}/${f.name}` : f.name;
                                            return (
                                                    <Postcard
                                                            key={idx}
                                                            src={f.url}
                                                            guid={f.user_guid}
                                                            displayName={f.display_name}
                                                            filename={f.name}
                                                            contentType={f.content_type}
                                                            onReport={() => handleReport(f.user_guid, name)}
                                                    />
                                            );
                                    })}
                            </Stack>
                    </div>
	    );
};

export default Gallery;
