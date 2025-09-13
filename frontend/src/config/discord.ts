export const discordConfig = {
        clientId: '000000000000000000',
        scope: 'identify email',
        redirectUri: `${window.location.origin}/userpage`,
        authorizeEndpoint: 'https://discord.com/oauth2/authorize',
};
export default discordConfig;
