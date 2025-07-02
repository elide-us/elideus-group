import { Box, Typography, Link } from '@mui/material';

const Home = (): JSX.Element => {
  // In a real app, these might be provided by your backend or environment
  const appVersion = "0.0.1"; // Replace with dynamic version if available
  const hostname = "elideusgroup.com"; // Replace with dynamic hostname if available

  return (
    <Box
      sx={{
        height: '100vh',
        margin: 0,
        backgroundColor: '#333',
        color: '#c1c1c1',
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
          sx={{ color: '#c1c1c1', textDecoration: 'none' }}
        >
          repo
        </Link>{' '}
        -{' '}
        <Link 
          href="https://github.com/elide-us/elideus-group/actions" 
          target="_blank" 
          rel="noopener noreferrer" 
          sx={{ color: '#c1c1c1', textDecoration: 'none' }}
        >
          build
        </Link>
      </Typography>
    </Box>
  );
};

export default Home;
