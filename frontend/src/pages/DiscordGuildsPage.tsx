import { useEffect, useState } from "react";
import {
        Box,
        Divider,
        Table,
        TableBody,
        TableCell,
        TableHead,
        TableRow,
        Typography,
} from "@mui/material";
import PageTitle from "../components/PageTitle";
import EditBox from "../components/EditBox";
import ColumnHeader from "../components/ColumnHeader";
import type { DiscordGuildsGuildItem1, DiscordGuildsList1 } from "../shared/RpcModels";
import { fetchListGuilds, fetchUpdateCredits } from "../rpc/discord/guilds";

const DiscordGuildsPage = (): JSX.Element => {
        const [guilds, setGuilds] = useState<DiscordGuildsGuildItem1[]>([]);
        const [forbidden, setForbidden] = useState(false);

        const loadGuilds = async (): Promise<void> => {
                try {
                        const res: DiscordGuildsList1 = await fetchListGuilds();
                        setGuilds(res.guilds ?? []);
                        setForbidden(false);
                } catch (e: any) {
                        if (e?.response?.status === 403) {
                                setForbidden(true);
                        } else {
                                setGuilds([]);
                        }
                }
        };

        useEffect(() => {
                void loadGuilds();
        }, []);

        if (forbidden) {
                return (
                        <Box sx={{ p: 2 }}>
                                <Typography variant="h6">Forbidden</Typography>
                        </Box>
                );
        }

        const updateCredits = async (index: number, credits: number): Promise<void> => {
                const updated = [...guilds];
                updated[index] = { ...updated[index], credits };
                setGuilds(updated);
                await fetchUpdateCredits({
                        guild_id: updated[index].guild_id,
                        credits,
                });
                void loadGuilds();
        };

        return (
                <Box sx={{ p: 2 }}>
                        <PageTitle>Discord Guild Management</PageTitle>
                        <Divider sx={{ mb: 2 }} />
                        <Table size="small" sx={{ "& td, & th": { py: 0.5, verticalAlign: "top" } }}>
                                <TableHead>
                                        <TableRow>
                                                <ColumnHeader>Name</ColumnHeader>
                                                <ColumnHeader>Guild ID</ColumnHeader>
                                                <ColumnHeader>Credits</ColumnHeader>
                                                <ColumnHeader>Member Count</ColumnHeader>
                                                <ColumnHeader>Joined</ColumnHeader>
                                                <ColumnHeader>Region</ColumnHeader>
                                                <ColumnHeader>Notes</ColumnHeader>
                                        </TableRow>
                                </TableHead>
                                <TableBody>
                                        {guilds.map((guild, index) => (
                                                <TableRow key={guild.recid}>
                                                        <TableCell>{guild.name}</TableCell>
                                                        <TableCell>{guild.guild_id}</TableCell>
                                                        <TableCell>
                                                                <EditBox
                                                                        value={guild.credits}
                                                                        onCommit={(value) => void updateCredits(index, Number(value))}
                                                                        width="80px"
                                                                />
                                                        </TableCell>
                                                        <TableCell>{guild.member_count ?? ""}</TableCell>
                                                        <TableCell>{guild.joined_on ?? ""}</TableCell>
                                                        <TableCell>{guild.region ?? ""}</TableCell>
                                                        <TableCell>{guild.notes ?? ""}</TableCell>
                                                </TableRow>
                                        ))}
                                </TableBody>
                        </Table>
                </Box>
        );
};

export default DiscordGuildsPage;
