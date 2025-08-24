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
import { Delete, Add } from "@mui/icons-material";
import RolesSelector from "./RolesSelector";
import type {
	SystemRoutesRouteItem1,
	SystemRoutesList1,
        ServiceRolesRoles1,
} from "./shared/RpcModels";
import {
	fetchRoutes,
	fetchUpsertRoute,
	fetchDeleteRoute,
} from "./rpc/system/routes";
import { fetchRoles } from "./rpc/service/roles";

const SystemRoutesPage = (): JSX.Element => {
	const [routes, setRoutes] = useState<SystemRoutesRouteItem1[]>([]);
	const [roleNames, setRoleNames] = useState<string[]>([]);
	const [newRoute, setNewRoute] = useState<SystemRoutesRouteItem1>({
		path: "",
		name: "",
		icon: "",
		sequence: 0,
		required_roles: [],
	});
		const [forbidden, setForbidden] = useState(false);
		const load = async (): Promise<void> => {
				try {
						const res: SystemRoutesList1 = await fetchRoutes();
						setRoutes(res.routes.sort((a, b) => a.sequence - b.sequence));
						console.debug("[SystemRoutesPage] loaded routes");
				} catch (e: any) {
						console.debug("[SystemRoutesPage] failed to load routes", e);
						if (e?.response?.status === 403) {
								setForbidden(true);
						} else {
								setRoutes([]);
						}
				}
				try {
                                                const roles: ServiceRolesRoles1 = await fetchRoles();
						setRoleNames(roles.roles);
						console.debug("[SystemRoutesPage] loaded roles");
				} catch (e: any) {
						console.debug("[SystemRoutesPage] failed to load roles", e);
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
				field: keyof SystemRoutesRouteItem1,
				value: any,
	): Promise<void> => {
				const updated = [...routes];
				(updated[index] as any)[field] = value;
				setRoutes(updated);
				console.debug("[SystemRoutesPage] updating route", updated[index]);
				await fetchUpsertRoute(updated[index]);
				void load();
		};

	const handleDelete = async (path: string): Promise<void> => {
				console.debug("[SystemRoutesPage] deleting route", path);
				await fetchDeleteRoute({ path });
				void load();
		};

	const handleAdd = async (): Promise<void> => {
		if (!newRoute.path) return;
				console.debug("[SystemRoutesPage] adding route", newRoute);
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
			<Typography variant="h5">System Routes</Typography>
			<Divider sx={{ mb: 2 }} />
			<Table size="small" sx={{ "& td, & th": { py: 0.5 } }}>
				<TableHead>
					<TableRow>
            <TableCell>Path</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Icon</TableCell>
            <TableCell>Sequence</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
      <TableBody>
                                        {routes.map((r, idx) => (
                                                <Fragment key={r.path}>
                                                        <TableRow sx={{ "& > *": { borderBottom: "none" } }}>
                                                               <TableCell>
                                                                        <TextField
                                                                                value={r.path}
                                                                                onChange={(e) =>
                                                                                        updateRoute(
                                                                                                idx,
                                                                                                "path",
                                                                                                e.target.value,
                                                                                        )
                                                                                }
                                                                        />
                                                                </TableCell>
                                                                <TableCell>
                                                                        <TextField
                                                                                value={r.name}
                                                                                onChange={(e) =>
                                                                                        updateRoute(
                                                                                                idx,
                                                                                                "name",
                                                                                                e.target.value,
                                                                                        )
                                                                                }
                                                                        />
                                                                </TableCell>
                                                                <TableCell>
                                                                        <TextField
                                                                                value={r.icon ?? ""}
                                                                                onChange={(e) =>
                                                                                        updateRoute(
                                                                                                idx,
                                                                                                "icon",
                                                                                                e.target.value,
                                                                                        )
                                                                                }
                                                                        />
                                                                </TableCell>
                                                                <TableCell>
                                                                        <TextField
                                                                                type="number"
                                                                                value={r.sequence}
                                                                                onChange={(e) =>
                                                                                        updateRoute(
                                                                                                idx,
                                                                                                "sequence",
                                                                                                Number(e.target.value),
                                                                                        )
                                                                                }
                                                                        />
                                                                </TableCell>
                                                                <TableCell>
                                                                        <IconButton
                                                                                onClick={() => handleDelete(r.path)}
                                                                        >
                                                                                <Delete />
                                                                        </IconButton>
                                                                </TableCell>
                                                        </TableRow>
                                                        <TableRow>
                                                                <TableCell colSpan={5}>
                                                                        <RolesSelector
                                                                                allRoles={roleNames}
                                                                                value={r.required_roles}
                                                                                onChange={(roles) =>
                                                                                        void updateRoute(
                                                                                                idx,
                                                                                                "required_roles",
                                                                                                roles,
                                                                                        )
                                                                                }
                                                                        />
                                                                </TableCell>
                                                        </TableRow>
                                                </Fragment>
                                        ))}
                                        <TableRow>
                                                <TableCell>
                                                        <TextField
								value={newRoute.path}
								onChange={(e) =>
									setNewRoute({
										...newRoute,
										path: e.target.value,
									})
								}
							/>
						</TableCell>
						<TableCell>
							<TextField
								value={newRoute.name}
								onChange={(e) =>
									setNewRoute({
										...newRoute,
										name: e.target.value,
									})
								}
							/>
						</TableCell>
						<TableCell>
							<TextField
								value={newRoute.icon ?? ""}
								onChange={(e) =>
									setNewRoute({
										...newRoute,
										icon: e.target.value,
									})
								}
							/>
						</TableCell>
						<TableCell>
							<TextField
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
                  <TableCell>
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
                  <TableCell>
                          <IconButton onClick={handleAdd}>
                                  <Add />
                          </IconButton>
                  </TableCell>
          </TableRow>
				</TableBody>
			</Table>
		</Box>
	);
};

export default SystemRoutesPage;
