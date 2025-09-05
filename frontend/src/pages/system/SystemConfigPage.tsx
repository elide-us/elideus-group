import { useEffect, useState, type JSX, type ReactNode } from 'react';
import {
    Autocomplete,
    Box,
    Button,
    Chip,
    MenuItem,
    Stack,
    Tab,
    Tabs,
    TextField,
    Typography,
} from '@mui/material';
import Notification from '../../components/Notification';
import PageTitle from '../../components/PageTitle';
import type { SystemConfigList1 } from '../../shared/RpcModels';
import { fetchConfigs, fetchUpsertConfig } from '../../rpc/system/config';

const AUTH_PROVIDERS = ['microsoft', 'discord', 'google', 'apple'];
const GUID_REGEX = /^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$/;
const HOSTNAME_REGEX = /^https:\/\/.+/;
const AZURE_BLOB_REGEX = /^(?!-)(?!.*--)[a-z0-9-]{3,63}(?<!-)$/;
const DISCORD_SNOWFLAKE = /^\d{17,20}$/;
const DISCORD_CHANNEL = /^#[a-z0-9-]{2,100}$/;
const REPO_REGEX = /^(https:\/\/|git@)/;
const SEMVER_REGEX = /^\d+\.\d+\.\d+(?:\+\d+)?$/;

interface TabPanelProps {
    children?: ReactNode;
    value: number;
    index: number;
}

const TabPanel = ({ children, value, index }: TabPanelProps): JSX.Element => (
    <div role="tabpanel" hidden={value !== index}>
        {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
);

const SystemConfigPage = (): JSX.Element => {
    const [config, setConfig] = useState<Record<string, string>>({});
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [tab, setTab] = useState(0);
    const [notification, setNotification] = useState(false);
    const [forbidden, setForbidden] = useState(false);

    const handleNotificationClose = (): void => {
        setNotification(false);
    };

    const load = async (): Promise<void> => {
        try {
            const res: SystemConfigList1 = await fetchConfigs();
            const map: Record<string, string> = {};
            res.items.forEach((i) => {
                map[i.key] = i.value;
            });
            setConfig(map);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            } else {
                setConfig({});
            }
        }
    };

    useEffect(() => {
        void load();
    }, []);

    const validate = (key: string, value: string): boolean => {
        let err = '';
        switch (key) {
            case 'AuthProviders': {
                const parts = value.split(',').map((p) => p.trim()).filter(Boolean);
                const unknown = parts.filter((p) => !AUTH_PROVIDERS.includes(p));
                if (unknown.length) err = `Unknown providers: ${unknown.join(', ')}`;
                break;
            }
            case 'Hostname':
                if (!HOSTNAME_REGEX.test(value) || /\/$/.test(value)) {
                    err = 'Must start with https and have no trailing slash.';
                }
                break;
            case 'MsApiId':
                if (!GUID_REGEX.test(value)) err = 'Invalid GUID.';
                break;
            case 'GoogleClientId':
                if (!value.endsWith('.apps.googleusercontent.com')) {
                    err = 'Should end with .apps.googleusercontent.com';
                }
                break;
            case 'JwksCacheTime':
                if (Number.isNaN(Number(value)) || Number(value) < 60) {
                    err = 'Must be >= 60.';
                }
                break;
            case 'AzureBlobContainerName':
                if (!AZURE_BLOB_REGEX.test(value)) err = 'Invalid container name.';
                break;
            case 'DiscordSyschan':
                if (!DISCORD_SNOWFLAKE.test(value) && !DISCORD_CHANNEL.test(value)) {
                    err = 'Must be snowflake or #channel-name';
                }
                break;
            case 'Repo':
                if (!REPO_REGEX.test(value)) err = 'Must be https:// or git@';
                break;
            case 'Version':
            case 'LastVersion':
                if (!SEMVER_REGEX.test(value)) err = 'Invalid semver.';
                break;
            default:
                break;
        }
        setErrors((prev) => ({ ...prev, [key]: err }));
        return !err;
    };

    const save = async (key: string, value: string): Promise<void> => {
        setConfig((prev) => ({ ...prev, [key]: value }));
        if (!validate(key, value)) return;
        await fetchUpsertConfig({ key, value });
        setNotification(true);
    };

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    const providers = (config.AuthProviders || '')
        .split(',')
        .map((p) => p.trim())
        .filter(Boolean);

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>System Configuration</PageTitle>
            <Tabs value={tab} onChange={(_e, v) => setTab(v)} aria-label="system config tabs">
                <Tab label="Authentication" />
                <Tab label="Storage" />
                <Tab label="Logging" />
                <Tab label="DevOps" />
            </Tabs>

            <TabPanel value={tab} index={0}>
                <Stack spacing={2} sx={{ maxWidth: 600 }}>
                    <Autocomplete
                        multiple
                        freeSolo
                        options={AUTH_PROVIDERS}
                        value={providers}
                        onChange={(_e, newValue) => {
                            const v = newValue.join(',');
                            void save('AuthProviders', v);
                        }}
                        renderTags={(value, getTagProps) =>
                            value.map((option, index) => {
                                const { key, ...tagProps } = getTagProps({ index });
                                return (
                                    <Chip
                                        key={key}
                                        {...tagProps}
                                        label={option}
                                        color={AUTH_PROVIDERS.includes(option) ? 'default' : 'error'}
                                    />
                                );
                            })
                        }
                        renderInput={(params) => (
                            <TextField
                                {...params}
                                label="AuthProviders"
                                error={Boolean(errors.AuthProviders)}
                                helperText={errors.AuthProviders}
                            />
                        )}
                    />
                    <TextField
                        label="Hostname"
                        type="url"
                        value={config.Hostname || ''}
                        onChange={(e) => save('Hostname', e.target.value.replace(/\/$/, ''))}
                        error={Boolean(errors.Hostname)}
                        helperText={errors.Hostname}
                    />
                    <TextField
                        label="MsApiId"
                        value={config.MsApiId || ''}
                        onChange={(e) => save('MsApiId', e.target.value)}
                        error={Boolean(errors.MsApiId)}
                        helperText={errors.MsApiId}
                    />
                    <Typography variant="caption">
                        Example: https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={
                            config.MsApiId || '<MsApiId>'
                        }
                    </Typography>
                    <TextField
                        label="GoogleClientId"
                        value={config.GoogleClientId || ''}
                        onChange={(e) => save('GoogleClientId', e.target.value)}
                        error={Boolean(errors.GoogleClientId)}
                        helperText={errors.GoogleClientId}
                    />
                    <Typography variant="caption">
                        https://accounts.google.com/o/oauth2/v2/auth?client_id={
                            config.GoogleClientId || '<GoogleClientId>'
                        }
                    </Typography>
                    <TextField
                        label="JwksCacheTime"
                        type="number"
                        value={config.JwksCacheTime || ''}
                        onChange={(e) => save('JwksCacheTime', e.target.value)}
                        error={Boolean(errors.JwksCacheTime)}
                        helperText={errors.JwksCacheTime || 'How often to refetch provider JWKS.'}
                    />
                </Stack>
            </TabPanel>

            <TabPanel value={tab} index={1}>
                <Stack spacing={2} sx={{ maxWidth: 600 }}>
                    <TextField
                        label="AzureBlobContainerName"
                        value={config.AzureBlobContainerName || ''}
                        onChange={(e) => save('AzureBlobContainerName', e.target.value)}
                        error={Boolean(errors.AzureBlobContainerName)}
                        helperText={errors.AzureBlobContainerName}
                    />
                </Stack>
            </TabPanel>

            <TabPanel value={tab} index={2}>
                <Stack spacing={2} sx={{ maxWidth: 600 }}>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <TextField
                            label="DiscordSyschan"
                            value={config.DiscordSyschan || ''}
                            onChange={(e) => save('DiscordSyschan', e.target.value)}
                            error={Boolean(errors.DiscordSyschan)}
                            helperText={errors.DiscordSyschan}
                            sx={{ flex: 1 }}
                        />
                        <Button variant="outlined" onClick={() => console.log('Test ping')}>
                            Test ping
                        </Button>
                    </Box>
                    <TextField
                        select
                        label="LoggingLevel"
                        value={config.LoggingLevel || ''}
                        onChange={(e) => save('LoggingLevel', e.target.value)}
                        helperText="Controls what is sent to DiscordSyschan."
                    >
                        {['error', 'warn', 'info', 'debug', 'trace'].map((l) => (
                            <MenuItem key={l} value={l}>
                                {l}
                            </MenuItem>
                        ))}
                    </TextField>
                </Stack>
            </TabPanel>

            <TabPanel value={tab} index={3}>
                <Stack spacing={2} sx={{ maxWidth: 600 }}>
                    <TextField
                        label="Repo"
                        type="url"
                        value={config.Repo || ''}
                        onChange={(e) => save('Repo', e.target.value)}
                        error={Boolean(errors.Repo)}
                        helperText={errors.Repo}
                    />
                    <TextField
                        label="Version"
                        value={config.Version || ''}
                        InputProps={{ readOnly: true }}
                        helperText="CI increases build automatically."
                    />
                    <TextField
                        label="LastVersion"
                        value={config.LastVersion || ''}
                        InputProps={{ readOnly: true }}
                        helperText="If MAJOR/MINOR increased since LastVersion, reset build to 0."
                    />
                </Stack>
            </TabPanel>

            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity="success"
                message="Saved"
            />
        </Box>
    );
};

export default SystemConfigPage;

