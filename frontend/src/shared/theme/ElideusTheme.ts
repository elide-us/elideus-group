import { createTheme, type Theme } from '@mui/material/styles';

const ElideusTheme: Theme = createTheme({
	palette: {
		mode: 'dark',
		primary: { main: '#90caf9' },
		secondary: { main: '#f48fb1' },
		background: { default: '#121212', paper: '#000000' },
		text: { primary: '#ffffff', secondary: '#b0b0c5' },
	},
	typography: {
		fontFamily: 'Roboto, Arial, sans-serif',
		h1: { fontSize: '1.6rem', fontWeight: 600 },
		h2: { fontSize: '1.35rem', fontWeight: 500 },
		body1: { fontSize: '0.875rem', lineHeight: 1.5 },
		body2: { fontSize: '0.8rem', lineHeight: 1.4 },
		button: { textTransform: 'none', fontSize: '0.8rem' },
	},
	components: {
		MuiCardMedia: {
			styleOverrides: {
				root: {
					maxWidth: '60%',
					marginBottom: '50px',
				},
			},
		},
		MuiTextField: {
			styleOverrides: {
				root: {
					margin: '8px',
					'& .MuiInputBase-input': {
						padding: '8px',
					},
				},
			},
		},
		MuiTypography: {
			variants: [
				{
					props: { variant: 'pageTitle' },
					style: {
						fontSize: '1.5rem',
						fontWeight: 600,
						marginBottom: '4px',
						textAlign: 'left',
						fontFamily: 'Georgia, "Times New Roman", serif',
						color: '#f5f5f2',
					},
				},
				{
					props: { variant: 'columnHeader' },
					style: {
						fontSize: '0.85rem',
						fontWeight: 700,
						fontFamily: 'Georgia, Times, "Times New Roman", serif',
						fontVariant: 'small-caps',
					},
				},
			],
		},
	},
});

export default ElideusTheme;
