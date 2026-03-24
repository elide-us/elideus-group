import { Box, Typography, Link as MuiLink, CardMedia, Button } from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import type { PublicLinksLinkItem1, PublicVarsVersions1 } from '../shared/RpcModels';
import Logo from '../assets/elideus_group_green.png';
import { fetchVersions } from '../rpc/public/vars';
import { fetchHomeLinks } from '../rpc/public/links';
import BottomBar from '../components/BottomBar';

const Home = (): JSX.Element => {
	const [info, setInfo] = useState<PublicVarsVersions1 | null>(null);
	const [links, setLinks] = useState<PublicLinksLinkItem1[]>([]);

	useEffect(() => {
		void (async () => {
			try {
				const versions = await fetchVersions();
				setInfo(versions);
			} catch {
				setInfo(null);
			}

			try {
				const homeLinks = await fetchHomeLinks();
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
				minHeight: 'calc(100vh - 28px)',
				backgroundColor: 'background.paper',
				pt: 2,
				px: 2,
			}}
		>
			<CardMedia
				component="img"
				alt="Elideus Group Image"
				image={Logo}
				sx={{ maxWidth: { xs: '75%', sm: '40%' }, marginBottom: '24px' }}
			/>
			<Typography variant="body1" sx={{ color: '#FFFFFF', textAlign: 'center' }}>
				AI Engineering and Consulting Services
			</Typography>
			<Box sx={{ mt: 2, width: '100%', maxWidth: 300, textAlign: 'center' }}>
				{links.map((link) => (
					<MuiLink
						key={link.title}
						href={link.url}
						title={link.title}
						underline="none"
						target="_blank"
						rel="noopener noreferrer"
						sx={{
							display: 'block',
							padding: '10px',
							margin: '8px 0',
							borderRadius: '4px',
							transition: 'background 0.3s',
							color: '#ffffff',
							backgroundColor: '#111',
							textDecoration: 'none',
							'&:hover': { backgroundColor: '#222' },
						}}
					>
						{link.title}
					</MuiLink>
				))}
				<Box
					sx={{
						mt: 2,
						display: 'flex',
						justifyContent: 'center',
						gap: 2,
						flexWrap: 'wrap',
					}}
				>
					<Button component={RouterLink} to="/terms-of-service" variant="outlined">
						Terms of Service
					</Button>
					<Button component={RouterLink} to="/privacy-policy" variant="outlined">
						Privacy Policy
					</Button>
				</Box>
			</Box>
			<Box sx={{ flexGrow: 1 }} />
			<BottomBar info={info} />
		</Box>
	);
};

export default Home;
