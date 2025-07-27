import { Box, Typography, Link, CardMedia } from '@mui/material';
import { useEffect, useState } from 'react';
import type { LinkItem } from './shared/RpcModels';
import Logo from './assets/elideus_group_green.png';
import {
        fetchHostname2 as fetchHostname,
        fetchVersion2 as fetchVersion,
        fetchRepo2 as fetchRepo,
        fetchFfmpegVersion,
} from './rpc/frontend/vars';
import { fetchHome2 as fetchHome } from './rpc/frontend/links';

const Home = (): JSX.Element => {
	const [hostname, setHostname] = useState('');
	const [version, setVersion] = useState('');
	const [repo, setRepo] = useState('');
	const [ffmpegVersion, setFfmpegVersion] = useState<string | null>(null);
	const [links, setLinks] = useState<LinkItem[]>([]);

	useEffect(() => {
		void (async () => {
			try {
				const host = await fetchHostname();
				const cleanHost = host.hostname.replace(/^"|"$/g, '');
				setHostname(cleanHost);
			} catch {
				setHostname('unknown');
			}

			try {
				const repoInfo = await fetchRepo();
				const cleanRepo = repoInfo.repo.replace(/^"|"$/g, '');
				setRepo(cleanRepo);
			} catch {
				setRepo('unknown');
			}

			try {
				const versionInfo = await fetchVersion();
				const cleanVersion = versionInfo.version.replace(/^"|"$/g, '');
				setVersion(cleanVersion);
			} catch {
				setVersion('v0.0.0');
			}

			try {
				const ffmpegInfo = await fetchFfmpegVersion();
				const cleanFfmpeg = ffmpegInfo.ffmpeg_version.replace(/^"|"$/g, '');
				setFfmpegVersion(cleanFfmpeg);
			} catch {
				setFfmpegVersion('unknown');
			}

			try {
				const homeLinks = await fetchHome();
				setLinks(homeLinks.links);
			} catch {
				setLinks([]);
			}
		})();
	}, []);

	return (
		<Box
			sx={{
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				justifyContent: 'flex-start',
				height: '100vh',
				backgroundColor: 'background.paper',
				paddingTop: '20px',
			}}
		>
			<CardMedia component="img" alt="Elideus Group Image" image={Logo} />
			<Typography variant="body1">AI Engineering and Consulting Services</Typography>
			<Box sx={{ marginTop: '20px', width: '300px', textAlign: 'center' }}>
				{links.map((link) => (
					<Link key={link.title}
						href={link.url}
						title={link.title}
						underline="none"
						target="_blank"
						rel="noopener noreferrer"
					>
						{link.title}
					</Link>
				))}
			</Box>
			<Typography variant="body1" sx={{ marginTop: '20px' }}>
				{version} running on {hostname}
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '4px' }}>
				{ffmpegVersion ? ffmpegVersion : 'Loading version...'}
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '4px' }}>
				GitHub:{' '}
				<Link
					href={repo}
					target="_blank"
					rel="noopener noreferrer"
					underline="none"
					sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
				>
					repo
				</Link>
					{' '}-{' '}
				<Link
					href={repo ? `${repo}/actions` : ''}
					target="_blank"
					rel="noopener noreferrer"
					underline="none"
					sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
				>
					build
				</Link>
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '20px' }}>
				Contact us at:{' '}
				<Link
					href="mailto:contact@elideusgroup.com"
					underline="none"
					sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
				>
					contact@elideusgroup.com
				</Link>
			</Typography>
		</Box>
	);
};

export default Home;
