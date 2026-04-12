export const discordConfig = {
        clientId: '1339726954986999878',
        scope: 'identify email openid',
        redirectUri: `${window.location.origin}`,
        authorizeEndpoint: 'https://discord.com/oauth2/authorize',
};

export const getDiscordAuthorizeUrl = (): string => {
        return `${discordConfig.authorizeEndpoint}?response_type=code&client_id=${discordConfig.clientId}&scope=${encodeURIComponent(discordConfig.scope)}&redirect_uri=${encodeURIComponent(discordConfig.redirectUri)}`;
};
export default discordConfig;
