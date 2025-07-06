import { Box, Typography, Link } from '@mui/material';
import { useEffect, useState } from 'react';
import { fetchHostname, fetchVersion, fetchRepo, fetchFfmpegVersion } from './rpcClient';

const Home = (): JSX.Element => {
  const [appVersion, setAppVersion] = useState('');
  const [hostname, setHostname] = useState('');
  const [repo, setRepo] = useState('');
  const [build, setBuild] = useState('');
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
        const cleanBuild = repoInfo.build.replace(/^"|"$/g, '');
        setRepo(cleanRepo);
        setBuild(cleanBuild);
      } catch {
        setRepo('');
        setBuild('');
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
        height: '100vh',
        margin: 0,
        bgcolor: 'background.paper',
        color: 'text.primary',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        p: 2,
      }}
    >
      <Typography
        variant="h1"
        sx={{ fontSize: '20vh', m: 0 }}
      >
        {"\\m/"}
      </Typography>
      <Typography sx={{ fontSize: 14, mt: 1 }}>
        v{appVersion} running on {hostname}
      </Typography>
      <Typography sx={{ fontSize: 14, mt: 1 }}>
        GitHub:{' '}
        <Link
          href={repo}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ color: 'text.primary', textDecoration: 'none' }}
        >
          repo
        </Link>{' '}
        -{' '}
        <Link
          href={build}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ color: 'text.primary', textDecoration: 'none' }}
        >
          build
        </Link>
      </Typography>
      <Typography sx={{ fontSize: 14, mt: 1 }}>
        {ffmpegVersion ? ffmpegVersion : 'Loading version...'}
      </Typography>
    </Box>
  );
};

export default Home;
