import { Box, Typography, Link } from '@mui/material';
import type { PublicVarsVersions1 } from '../shared/RpcModels';

interface Props {
	info: PublicVarsVersions1 | null;
}

const BottomBar = ({ info }: Props): JSX.Element => {
	return (
		<Box sx={{ textAlign: 'center', padding: '20px' }}>
			{info ? (
				<>
					<Typography variant="body1">
						{info.version} running on {info.hostname}
					</Typography>
					{info.ffmpeg_version && (
						<Typography variant="body1" sx={{ marginTop: '4px' }}>
							{info.ffmpeg_version}
						</Typography>
					)}
					{info.odbc_version && (
						<Typography variant="body1" sx={{ marginTop: '4px' }}>
							{info.odbc_version}
						</Typography>
					)}
					{info.repo && (
						<Typography variant="body1" sx={{ marginTop: '4px' }}>
							GitHub{' '}
							<Link
								href={info.repo}
								target="_blank"
								rel="noopener noreferrer"
								underline="none"
								sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
								>
									repo
								</Link>
								{' '}-{' '}
								<Link
									href={`${info.repo}/actions`}
									target="_blank"
									rel="noopener noreferrer"
									underline="none"
									sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
									>
										build
									</Link>
							</Typography>
					)}
				</>
			) : null}
			<Typography variant="body1" sx={{ marginTop: info ? '20px' : '0px' }}>
				Contact us at{' '}
				<Link
					href="mailto:contact@elideusgroup.com"
					underline="none"
					sx={{ display: 'inline', padding: 0, margin: 0, backgroundColor: 'transparent' }}
					>
					contact@elideusgroup.com
				</Link>
			</Typography>
			<Typography variant="body1" sx={{ marginTop: '4px', width: '300px', mx: 'auto' }}>
				<Link href="/privacy-policy" underline="none" sx={{ display: 'block' }}>Privacy Policy</Link>
			</Typography>
	</Box>
);
};

export default BottomBar;
