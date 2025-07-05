import { createTheme, Theme } from '@mui/material/styles';

const ElideusTheme: Theme = createTheme({
	palette: {
		mode: 'dark',
		primary: { main: '#90caf9' },
		secondary: { main: '#f48fb1' },
                background: { default: '#121212', paper: '#000000' },
		text: { primary: '#ffffff', secondary: '#b0b0c5' }
	},
	typography: {
		fontFamily: 'Roboto, Arial, sans-serif',
		h1: { fontSize: '2rem', fontWeight: 500 },
		h2: { fontSize: '1.75rem', fontWeight: 500 },
		body1: { fontSize: '1rem', lineHeight: 1.5 },
		button: { textTransform: 'none' }
	}
});

export default ElideusTheme;
