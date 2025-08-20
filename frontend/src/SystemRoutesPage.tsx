import { useEffect, useState } from "react";
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
	Stack,
	List,
	ListItemButton,
	ListItemText,
	Typography,
} from "@mui/material";
import {
	Delete,
	Add,
	ArrowForwardIos,
	ArrowBackIos,
} from "@mui/icons-material";
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

const MAX_HEIGHT = 120;

const SystemRoutesPage = (): JSX.Element => {
	const [routes, setRoutes] = useState<SystemRoutesRouteItem1[]>([]);
	const [roleNames, setRoleNames] = useState<string[]>([]);
	const [selectedLeft, setSelectedLeft] = useState<Record<number, string>>(
		{},
	);
	const [selectedRight, setSelectedRight] = useState<Record<number, string>>(
		{},
	);
	const [newRoute, setNewRoute] = useState<SystemRoutesRouteItem1>({
		path: "",
		name: "",
		icon: "",
		sequence: 0,
		required_roles: [],
	});
		const [newLeft, setNewLeft] = useState<string | null>(null);
		const [newRight, setNewRight] = useState<string | null>(null);
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

	const moveRight = async (idx: number): Promise<void> => {
		const role = selectedLeft[idx];
		if (!role) return;
		const updatedRoles = [...routes[idx].required_roles, role];
				setSelectedLeft({ ...selectedLeft, [idx]: "" });
				await updateRoute(idx, "required_roles", updatedRoles);
				console.debug("[SystemRoutesPage] moved role to required", role);
		};

	const moveLeft = async (idx: number): Promise<void> => {
		const role = selectedRight[idx];
		if (!role) return;
		const updatedRoles = routes[idx].required_roles.filter(
			(r) => r !== role,
		);
				setSelectedRight({ ...selectedRight, [idx]: "" });
				await updateRoute(idx, "required_roles", updatedRoles);
				console.debug("[SystemRoutesPage] removed role from required", role);
		};

	const handleDelete = async (path: string): Promise<void> => {
				console.debug("[SystemRoutesPage] deleting route", path);
				await fetchDeleteRoute({ path });
				void load();
		};

	const addMoveRight = (role: string | null): void => {
		if (!role) return;
				setNewRoute({
						...newRoute,
						required_roles: [...newRoute.required_roles, role],
				});
				console.debug("[SystemRoutesPage] added role to new route", role);
				setNewLeft(null);
		};

	const addMoveLeft = (role: string | null): void => {
		if (!role) return;
				setNewRoute({
						...newRoute,
						required_roles: newRoute.required_roles.filter((r) => r !== role),
				});
				console.debug("[SystemRoutesPage] removed role from new route", role);
				setNewRight(null);
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
		setNewLeft(null);
		setNewRight(null);
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
						<TableCell>Roles</TableCell>
						<TableCell />
					</TableRow>
				</TableHead>
				<TableBody>
					{routes.map((r, idx) => {
						const available = roleNames.filter(
							(n) => !r.required_roles.includes(n),
						);
						return (
							<TableRow key={r.path}>
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
									<Stack direction="row" spacing={1}>
										<List
											sx={{
												width: 120,
												maxHeight: MAX_HEIGHT,
												overflow: "auto",
												border: 1,
											}}
										>
											{available.map((role) => (
												<ListItemButton
													key={role}
													selected={
														selectedLeft[idx] ===
														role
													}
													onClick={() =>
														setSelectedLeft({
															...selectedLeft,
															[idx]: role,
														})
													}
												>
													<ListItemText
														primary={role}
													/>
												</ListItemButton>
											))}
										</List>
										<Stack
											spacing={1}
											justifyContent="center"
										>
											<IconButton
												onClick={() =>
													void moveRight(idx)
												}
											>
												<ArrowForwardIos />
											</IconButton>
											<IconButton
												onClick={() =>
													void moveLeft(idx)
												}
											>
												<ArrowBackIos />
											</IconButton>
										</Stack>
										<List
											sx={{
												width: 120,
												maxHeight: MAX_HEIGHT,
												overflow: "auto",
												border: 1,
											}}
										>
											{r.required_roles.map((role) => (
												<ListItemButton
													key={role}
													selected={
														selectedRight[idx] ===
														role
													}
													onClick={() =>
														setSelectedRight({
															...selectedRight,
															[idx]: role,
														})
													}
												>
													<ListItemText
														primary={role}
													/>
												</ListItemButton>
											))}
										</List>
									</Stack>
								</TableCell>
								<TableCell>
									<IconButton
										onClick={() => handleDelete(r.path)}
									>
										<Delete />
									</IconButton>
								</TableCell>
							</TableRow>
						);
					})}
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
							<Stack direction="row" spacing={1}>
								<List
									sx={{
										width: 120,
										maxHeight: MAX_HEIGHT,
										overflow: "auto",
										border: 1,
									}}
								>
									{roleNames
										.filter(
											(r) =>
												!newRoute.required_roles.includes(
													r,
												),
										)
										.map((role) => (
											<ListItemButton
												key={role}
												selected={newLeft === role}
												onClick={() => setNewLeft(role)}
											>
												<ListItemText primary={role} />
											</ListItemButton>
										))}
								</List>
								<Stack spacing={1} justifyContent="center">
									<IconButton
										onClick={() => addMoveRight(newLeft)}
									>
										<ArrowForwardIos />
									</IconButton>
									<IconButton
										onClick={() => addMoveLeft(newRight)}
									>
										<ArrowBackIos />
									</IconButton>
								</Stack>
								<List
									sx={{
										width: 120,
										maxHeight: MAX_HEIGHT,
										overflow: "auto",
										border: 1,
									}}
								>
									{newRoute.required_roles.map((role) => (
										<ListItemButton
											key={role}
											selected={newRight === role}
											onClick={() => setNewRight(role)}
										>
											<ListItemText primary={role} />
										</ListItemButton>
									))}
								</List>
							</Stack>
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
