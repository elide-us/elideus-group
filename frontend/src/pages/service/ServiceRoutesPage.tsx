import { useEffect, useState, Fragment } from "react";
import {
                Box,
                Divider,
                Table,
                TableHead,
                TableRow,
                TableCell,
                TableBody,
                TextField,
                IconButton,
                Typography,
                                } from "@mui/material";
import PageTitle from "../../components/PageTitle";
import { Delete, Add } from "@mui/icons-material";
import RolesSelector from "../../components/RolesSelector";
import EditBox from "../../components/EditBox";
import ColumnHeader from "../../components/ColumnHeader";
import type {
        ServiceRoutesRouteItem1,
        ServiceRoutesList1,
        ServiceRolesList1,
} from "../../shared/RpcModels";
import {
        fetchRoutes,
        fetchUpsertRoute,
        fetchDeleteRoute,
} from "../../rpc/service/routes";
import { fetchRoles } from "../../rpc/service/roles";

const ServiceRoutesPage = (): JSX.Element => {
        const [routes, setRoutes] = useState<ServiceRoutesRouteItem1[]>([]);
	const [roleNames, setRoleNames] = useState<string[]>([]);
        const [newRoute, setNewRoute] = useState<ServiceRoutesRouteItem1>({
		path: "",
		name: "",
		icon: "",
		sequence: 0,
		required_roles: [],
	});
		const [forbidden, setForbidden] = useState(false);
		const load = async (): Promise<void> => {
                                try {
                                                const res: ServiceRoutesList1 = await fetchRoutes();
                                                setRoutes(res.routes.sort((a, b) => a.sequence - b.sequence));
                                                console.debug("[ServiceRoutesPage] loaded routes");
                                } catch (e: any) {
                                                console.debug("[ServiceRoutesPage] failed to load routes", e);
						if (e?.response?.status === 403) {
								setForbidden(true);
						} else {
								setRoutes([]);
						}
				}
                                try {
                                        const roles: ServiceRolesList1 = await fetchRoles();
                                                setRoleNames(roles.roles.map((r) => r.name));
                                                console.debug("[ServiceRoutesPage] loaded roles");
                                } catch (e: any) {
                                                console.debug("[ServiceRoutesPage] failed to load roles", e);
                                                if (e?.response?.status === 403) {
                                                                setForbidden(true);
                                                } else {
                                                                setRoleNames([]);
                                                }
                                }
                };

		useEffect(() => {
				void load();
		}, []);

		if (forbidden) {
				return (
						<Box sx={{ p: 2 }}>
								<Typography variant="h6">Forbidden</Typography>
						</Box>
				);
		}

		const updateRoute = async (
				index: number,
                                field: keyof ServiceRoutesRouteItem1,
				value: any,
	): Promise<void> => {
				const updated = [...routes];
				(updated[index] as any)[field] = value;
				setRoutes(updated);
                                console.debug("[ServiceRoutesPage] updating route", updated[index]);
				await fetchUpsertRoute(updated[index]);
				void load();
		};

	const handleDelete = async (path: string): Promise<void> => {
                                console.debug("[ServiceRoutesPage] deleting route", path);
				await fetchDeleteRoute({ path });
				void load();
		};

	const handleAdd = async (): Promise<void> => {
		if (!newRoute.path) return;
                                console.debug("[ServiceRoutesPage] adding route", newRoute);
				await fetchUpsertRoute(newRoute);
				setNewRoute({
								path: "",
								name: "",
								icon: "",
								sequence: 0,
								required_roles: [],
				});
				void load();
		};

	return (
		<Box sx={{ p: 2 }}>
                        <PageTitle>Service Routes</PageTitle>
                        <Divider sx={{ mb: 2 }} />
                        <Table size="small" sx={{ "& td, & th": { py: 0.5 } }}>
                                <TableHead>
                                        <TableRow>
                                                <ColumnHeader sx={{ width: '30%' }}>Path</ColumnHeader>
                                                <ColumnHeader sx={{ width: '30%' }}>Name</ColumnHeader>
                                                <ColumnHeader sx={{ width: '20%' }}>Icon</ColumnHeader>
                                                <ColumnHeader sx={{ width: '15%' }}>Sequence</ColumnHeader>
                                                <ColumnHeader sx={{ width: '5%' }} />
                                        </TableRow>
                                </TableHead>
                                <TableBody>
										{routes.map((r, idx) => (
												<Fragment key={r.path}>
														<TableRow sx={{ "& > *": { borderBottom: 'none' } }}>
																<TableCell sx={{ width: '30%' }}>
																		<EditBox
																				value={r.path}
																				onCommit={(val) =>
																						updateRoute(idx, 'path', val)
																				}
																				width="95%"
																		/>
																</TableCell>
																<TableCell sx={{ width: '30%' }}>
																		<EditBox
																				value={r.name}
																				onCommit={(val) =>
																						updateRoute(idx, 'name', val)
																				}
																				width="95%"
																		/>
																</TableCell>
																<TableCell sx={{ width: '20%' }}>
																		<EditBox
																				value={r.icon ?? ''}
																				onCommit={(val) =>
																						updateRoute(idx, 'icon', val)
																				}
																				width="95%"
																		/>
																</TableCell>
																<TableCell sx={{ width: '15%' }}>
																		<EditBox
																				value={r.sequence}
																				onCommit={(val) =>
																						updateRoute(idx, 'sequence', val)
																				}
																				width="95%"
																		/>
																</TableCell>
																<TableCell sx={{ width: '5%' }}>
																		<IconButton onClick={() => handleDelete(r.path)}>
																				<Delete />
																		</IconButton>
																</TableCell>
														</TableRow>
														<TableRow>
																<TableCell colSpan={4}>
																		<RolesSelector
																				allRoles={roleNames}
																				value={r.required_roles}
																				onChange={(roles) =>
																						void updateRoute(idx, 'required_roles', roles)
																				}
																		/>
																</TableCell>
																<TableCell sx={{ width: '5%' }} />
														</TableRow>
												</Fragment>
										))}
										<TableRow>
												<TableCell sx={{ width: '30%' }}>
<TextField
sx={{ width: '95%' }}
value={newRoute.path}
				onChange={(e) =>
				setNewRoute({
					...newRoute,
					path: e.target.value,
				})
				}
			/>
												</TableCell>
												<TableCell sx={{ width: '30%' }}>
<TextField
sx={{ width: '95%' }}
value={newRoute.name}
				onChange={(e) =>
				setNewRoute({
					...newRoute,
					name: e.target.value,
				})
				}
			/>
												</TableCell>
												<TableCell sx={{ width: '20%' }}>
<TextField
sx={{ width: '95%' }}
value={newRoute.icon ?? ''}
				onChange={(e) =>
				setNewRoute({
					...newRoute,
					icon: e.target.value,
				})
				}
			/>
												</TableCell>
												<TableCell sx={{ width: '15%' }}>
<TextField
sx={{ width: '95%' }}
type="number"
value={newRoute.sequence}
				onChange={(e) =>
				setNewRoute({
					...newRoute,
					sequence: Number(e.target.value),
				})
				}
			/>
												</TableCell>
												<TableCell sx={{ width: '5%' }}>
														<IconButton onClick={handleAdd}>
																<Add />
														</IconButton>
												</TableCell>
										</TableRow>
										<TableRow>
												<TableCell colSpan={4}>
														<RolesSelector
																allRoles={roleNames}
																value={newRoute.required_roles}
																onChange={(roles) =>
																		setNewRoute({
																				...newRoute,
																				required_roles: roles,
																		})
																}
														/>
												</TableCell>
												<TableCell sx={{ width: '5%' }} />
										</TableRow>
								</TableBody>
						</Table>
		</Box>
	);
				};

export default ServiceRoutesPage;
