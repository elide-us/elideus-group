export const msalConfig = {
       auth: {
               clientId: '6c725f5b-6a44-4bf0-a0d6-c2cfc15230be',
               authority: 'https://login.microsoftonline.com/consumers',
               redirectUri: window.location.origin,
       },
};

export const loginRequest = {
       scopes: ['User.Read'],
};
