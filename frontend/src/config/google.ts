export const googleConfig = {
	clientId:
		import.meta.env.VITE_GOOGLE_CLIENT_ID ||
		'295304659309-vkbjt5572fg3vjlqbj3qkkfgal83pcrj.apps.googleusercontent.com',
	scope: 'openid profile email',
};
export default googleConfig;
