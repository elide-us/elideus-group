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
	},
	components: {
		MuiCardMedia: {
			styleOverrides: {
				root: {
					maxWidth: '60%',
					marginBottom: '50px'
				}
			}
		},
                MuiLink: {
                        styleOverrides: {
                                root: {
                                        display: 'block',
                                        padding: '12px',
                                        margin: '10px 0',
                                        borderRadius: '5px',
                                        transition: 'background 0.3s',
                                        color: '#ffffff',
                                        backgroundColor: '#111',
                                        textDecoration: 'none',
                                        '&:hover': {
                                                backgroundColor: '#222'
                                        }
                                }
                        }
                },
                MuiTextField: {
                        styleOverrides: {
                                root: {
                                        margin: '8px',
                                        '& .MuiInputBase-input': {
                                                padding: '8px'
                                        }
                                }
                        }
                },
                MuiTypography: {
                        variants: [
                                {
                                        props: { variant: 'pageTitle' },
                                        style: {
                                                fontSize: '2rem',
                                                fontWeight: 700,
                                                marginBottom: '30px',
                                                textAlign: 'right',
                                                fontFamily: 'Georgia, "Times New Roman", serif',
                                                color: '#f5f5f2'
                                        }
                                },
                                {
                                        props: { variant: 'columnHeader' },
                                        style: {
                                                fontSize: '0.85rem',
                                                fontWeight: 700,
                                                fontFamily: 'Georgia, Times, "Times New Roman", serif',
                                                fontVariant: 'small-caps'
                                        }
                                }
                        ]
                }
        }
});

export default ElideusTheme;
