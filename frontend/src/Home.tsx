import { Box, Typography, Link, CardMedia } from '@mui/material';
import { useEffect, useState } from 'react';
import Links from './config/links';
import Logo from './assets/elideus_group_green.png';
import {
	fetchHostname,
	fetchVersion,
	fetchRepo,
	fetchFfmpegVersion,
} from './rpcClient';

const Home = (): JSX.Element => {
	const [appVersion, setAppVersion] = useState('');
	const [hostname, setHostname] = useState('');
	const [repo, setRepo] = useState('');
	const [ffmpegVersion, setFfmpegVersion] = useState<string | null>(null);

	useEffect(() => {
		void (async () => {
			try {
				const version = await fetchVersion();
				const cleanVersion = version.version.replace(/^"|"$/g, '');
				setAppVersion(cleanVersion);
			} catch {
				setAppVersion('unknown');
			}

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
				setRepo('');
			}

			try {
				const ffmpegInfo = await fetchFfmpegVersion();
				const cleanFfmpeg = ffmpegInfo.ffmpeg_version.replace(/^"|"$/g, '');
				setFfmpegVersion(cleanFfmpeg);
			} catch {
				setFfmpegVersion('unknown');
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
				{Links.map((link) => (
					<Link
						key={link.title}
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
				v{appVersion} running on {hostname}
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '4px' }}>
				GitHub:{' '}
				<Link href={repo} target="_blank" rel="noopener noreferrer">
					repo
				</Link>
				{' '}-{' '}
				<Link href={repo ? `${repo}/actions` : ''} target="_blank" rel="noopener noreferrer">
					build
				</Link>
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '4px' }}>
				{ffmpegVersion ? ffmpegVersion : 'Loading version...'}
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '20px' }}>
				Contact us at:{' '}
				<Link underline="hover" href="mailto:contact@elideusgroup.com">
					contact@elideusgroup.com
				</Link>
			</Typography>
		</Box>
	);
};

export default Home;
