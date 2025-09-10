import { useEffect, useState, type JSX } from 'react';
import { useParams } from 'react-router-dom';
import { Avatar, Stack, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';
import { fetchProfile, fetchPublishedFiles } from '../rpc/public/users';
import type { PublicUsersProfile1, PublicUsersPublishedFile1 } from '../shared/RpcModels';

const PublicProfile = (): JSX.Element => {
    const { guid } = useParams();
    const [profile, setProfile] = useState<PublicUsersProfile1 | null>(null);
    const [files, setFiles] = useState<PublicUsersPublishedFile1[]>([]);

    useEffect(() => {
        if (!guid) return;
        void (async () => {
            try {
                const p = await fetchProfile({ guid });
                setProfile(p as PublicUsersProfile1);
            } catch {
                setProfile(null);
            }
            try {
                const f = await fetchPublishedFiles({ guid });
                setFiles((f as any).files ?? []);
            } catch {
                setFiles([]);
            }
        })();
    }, [guid]);

    return (
        <div>
            <PageTitle>User Profile</PageTitle>
            {profile && (
                <Stack spacing={2} alignItems="center" sx={{ mb: 4 }}>
                    <Avatar
                        src={profile.profile_image ? `data:image/png;base64,${profile.profile_image}` : undefined}
                        sx={{ width: 80, height: 80 }}
                    />
                    <Typography variant="h5">{profile.display_name}</Typography>
                    {profile.email && <Typography>{profile.email}</Typography>}
                </Stack>
            )}
            <Typography variant="h6" gutterBottom>
                Published Files
            </Typography>
            <ul>
                {files.map((f, idx) => (
                    <li key={idx}>{f.filename}</li>
                ))}
            </ul>
        </div>
    );
};

export default PublicProfile;
