import { Box, Typography, Link, CardMedia } from '@mui/material';
import { useEffect, useState } from 'react';
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
                        <Box sx={{ flexGrow: 1 }} />
                        <BottomBar info={info} />
                </Box>
        );
};

export default Home;
