import { Box, Typography, Link } from '@mui/material';
import { useEffect, useState } from 'react';
import { fetchHostname, fetchVersion } from './rpcClient';

const Home = (): JSX.Element => {
  const [appVersion, setAppVersion] = useState('');
  const [hostname, setHostname] = useState('');

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
          href="https://github.com/elide-us/elideus-group"
          target="_blank"
          rel="noopener noreferrer"
          sx={{ color: 'text.primary', textDecoration: 'none' }}
        >
          repo
        </Link>{' '}
        -{' '}
        <Link
          href="https://github.com/elide-us/elideus-group/actions"
          target="_blank"
          rel="noopener noreferrer"
          sx={{ color: 'text.primary', textDecoration: 'none' }}
        >
          build
        </Link>
      </Typography>
    </Box>
  );
};

export default Home;
