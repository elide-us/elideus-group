import { useContext, useEffect, useState, ChangeEvent } from "react";
import {
    Box,
    Typography,
    FormControlLabel,
    Switch,
    Avatar,
    Button,
    Stack,
    RadioGroup,
    Radio
} from "@mui/material";
import { PublicClientApplication } from "@azure/msal-browser";
import UserContext from "../shared/UserContext";
import type { UsersProfileProfile1 } from "../shared/RpcModels";
import {
    fetchProfile,
    fetchSetDisplay,
    fetchSetOptin
} from "../rpc/users/profile";
import {
    fetchSetProvider,
    fetchLinkProvider,
    fetchUnlinkProvider
} from "../rpc/users/providers";
import googleConfig from "../config/google";
import { msalConfig, loginRequest } from "../config/msal";
import EditBox from "../components/EditBox";

declare global {
  interface Window {
    google: any;
  }
}

const pca = new PublicClientApplication(msalConfig);

const UserPage = (): JSX.Element => {
    const { userData, setUserData, clearUserData } = useContext(UserContext);
    const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
    const [displayEmail, setDisplayEmail] = useState(false);
    const [displayName, setDisplayName] = useState("");
    const [provider, setProvider] = useState("microsoft");
    const [providers, setProviders] = useState<string[]>([]);

  const normalizeGuid = (guid: unknown): string => {
    if (typeof guid === "string") return guid;
    if (guid && typeof guid === "object") {
      const val = (guid as { toString?: () => string }).toString;
      if (val) {
        try {
          return val.call(guid);
        } catch {
          /* ignore */
        }
      }
    }
    return "";
  };

  useEffect(() => {
    if (!userData) return;
    void (async () => {
      try {
        const res: any = await fetchProfile();
        const profileData: UsersProfileProfile1 = {
          ...res,
          guid: normalizeGuid(res.guid)
        };
        setProfile(profileData);
        setDisplayName(profileData.display_name);
        setDisplayEmail(profileData.display_email);
        setProvider(profileData.default_provider);
        setProviders(profileData.auth_providers?.map((p) => p.name) ?? []);
      } catch {
        setProfile(null);
      }
    })();
  }, [userData]);

    const handleToggle = async (): Promise<void> => {
        const next = !displayEmail;
        setDisplayEmail(next);
        try {
            await fetchSetOptin({ display_email: next });
            if (profile) setProfile({ ...profile, display_email: next });
        } catch (err) {
            console.error("Failed to update email display", err);
        }
    };

    const commitDisplayName = async (val: string | number): Promise<void> => {
        const name = String(val);
        setDisplayName(name);
        try {
            await fetchSetDisplay({ display_name: name });
            if (userData) setUserData({ ...userData, display_name: name });
            if (profile) setProfile({ ...profile, display_name: name });
        } catch (err) {
            console.error("Failed to update display name", err);
        }
    };

    const handleProviderChange = async (e: ChangeEvent<HTMLInputElement>): Promise<void> => {
        const prev = provider;
        const next = e.target.value;
        setProvider(next);
        try {
            if (next === "google") {
                if (!window.google) throw new Error("Google API not loaded");
                const code = await new Promise<string>((resolve) => {
                    const cfg = {
                        client_id: googleConfig.clientId,
                        scope: googleConfig.scope,
                        redirect_uri: googleConfig.redirectUri,
                        callback: (resp: any) => resolve(resp.code)
                    };
                    const client = window.google.accounts.oauth2.initCodeClient(cfg);
                    client.requestCode();
                });
                await fetchSetProvider({ provider: next, code });
            } else if (next === "microsoft") {
                await pca.initialize();
                const loginResponse = await pca.loginPopup(loginRequest);
                const { idToken, accessToken } = loginResponse;
                await fetchSetProvider({
                    provider: next,
                    id_token: idToken,
                    access_token: accessToken
                });
            } else {
                await fetchSetProvider({ provider: next });
            }
            const res: any = await fetchProfile();
            const profileData: UsersProfileProfile1 = {
                ...res,
                guid: normalizeGuid(res.guid)
            };
            setProfile(profileData);
            setDisplayName(profileData.display_name);
            setDisplayEmail(profileData.display_email);
            setProviders(profileData.auth_providers?.map((p) => p.name) ?? []);
            if (userData) setUserData({ ...userData, display_name: profileData.display_name });
        } catch (err) {
            console.error("Failed to set provider", err);
            setProvider(prev);
        }
    };

  const handleUnlink = async (name: string): Promise<void> => {
    const isLast = providers.length <= 1;
    if (isLast && !window.confirm("This will delete your account. Continue?"))
      return;
    try {
      let newDefault: string | undefined;
      if (!isLast && provider === name)
        newDefault = providers.find((p) => p !== name);
      await fetchUnlinkProvider(
        newDefault
          ? { provider: name, new_default: newDefault }
          : { provider: name }
      );
      const updated = providers.filter((p) => p !== name);
      setProviders(updated);
      if (profile) {
        const authProviders =
          profile.auth_providers?.filter((p) => p.name !== name) ?? [];
        const updatedProfile = {
          ...profile,
          auth_providers: authProviders,
        };
        if (newDefault) updatedProfile.default_provider = newDefault;
        setProfile(updatedProfile);
      }
      if (newDefault) setProvider(newDefault);
      if (updated.length === 0) clearUserData();
    } catch (err) {
      console.error("Failed to unlink provider", err);
    }
  };

  const handleLink = async (name: string): Promise<void> => {
    if (name !== "microsoft" && name !== "google") return;
    try {
      if (name === "google") {
        if (!window.google) throw new Error("Google API not loaded");
        const code = await new Promise<string>((resolve) => {
          const codeClientConfig = {
            client_id: googleConfig.clientId,
            scope: googleConfig.scope,
            redirect_uri: googleConfig.redirectUri,
            callback: (resp: any) => resolve(resp.code)
          };
          console.debug("[UserPage] initCodeClient config", codeClientConfig);
          const client =
            window.google.accounts.oauth2.initCodeClient(codeClientConfig);
          client.requestCode();
        });
        console.debug("[UserPage] authorization code received", code);
        await fetchLinkProvider({ provider: name, code });
      } else {
        await pca.initialize();
        const loginResponse = await pca.loginPopup(loginRequest);
        const { idToken, accessToken } = loginResponse;
        await fetchLinkProvider({
          provider: name,
          id_token: idToken,
          access_token: accessToken
        });
      }
      const updated = [...providers, name];
      setProviders(updated);
      if (profile) {
        const authProviders = [
          ...(profile.auth_providers ?? []),
          { name, display: name.charAt(0).toUpperCase() + name.slice(1) }
        ];
        setProfile({ ...profile, auth_providers: authProviders });
      }
    } catch (err) {
      console.error("Link provider not implemented", err);
    }
  };

  const allProviders = [
    { name: "microsoft", display: "Microsoft", enabled: true },
    { name: "google", display: "Google", enabled: true },
    { name: "discord", display: "Discord", enabled: false },
    { name: "apple", display: "Apple", enabled: false }
  ];

  return (
    <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
      <Box sx={{ maxWidth: 400, width: "100%" }}>
        <Stack
          spacing={2}
          sx={{
            mt: 2,
            display: "flex",
            alignItems: "flex-end",
            textAlign: "right"
          }}
        >
          <Typography variant="h5" gutterBottom>
            User Profile
          </Typography>

          {profile && (
            <Stack
              spacing={2}
              sx={{ mt: 2, alignItems: "flex-end", width: "100%" }}
            >
              <Avatar
                src={
                  profile.profile_image
                    ? `data:image/png;base64,${profile.profile_image}`
                    : undefined
                }
                sx={{ width: 80, height: 80 }}
              />

              <EditBox value={displayName} onCommit={commitDisplayName} />

              <Typography>Credits: {profile.credits ?? 0}</Typography>
              <Typography>Email: {profile.email}</Typography>

              <RadioGroup
                value={provider}
                onChange={(e) => { void handleProviderChange(e); }}
                sx={{ alignItems: "flex-end" }}
              >
                {allProviders
                  .filter((p) => p.enabled && providers.includes(p.name))
                  .map((p) => (
                    <FormControlLabel
                      key={p.name}
                      value={p.name}
                      control={<Radio />}
                      label={p.display}
                    />
                  ))}
              </RadioGroup>

              {allProviders.map((p) => {
                const linked = providers.includes(p.name);
                return (
                  <Stack
                    key={p.name}
                    direction="row"
                    spacing={1}
                    sx={{ justifyContent: "flex-end", width: "100%" }}
                  >
                    <Typography>{p.display}</Typography>
                    {linked ? (
                      <Button
                        variant="outlined"
                        onClick={() => handleUnlink(p.name)}
                      >
                        {providers.length === 1 ? "Delete" : "Unlink"}
                      </Button>
                    ) : (
                      <Button
                        variant="contained"
                        onClick={() => handleLink(p.name)}
                        disabled={!p.enabled}
                      >
                        {p.enabled ? "Link" : "Link (Coming Soon)"}
                      </Button>
                    )}
                  </Stack>
                );
              })}

              <FormControlLabel
                control={
                  <Switch
                    checked={displayEmail}
                    onChange={() => {
                      void handleToggle();
                    }}
                  />
                }
                label="Display email publicly"
                labelPlacement="start"
                sx={{ alignSelf: "flex-end" }}
              />

            </Stack>
          )}
        </Stack>
      </Box>
    </Box>
  );
};

export default UserPage;
