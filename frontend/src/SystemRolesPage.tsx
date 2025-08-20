import { useEffect, useState } from "react";
import {
  Box,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  IconButton,
  TextField,
  Typography,
} from "@mui/material";
import { Delete, Add, ArrowUpward, ArrowDownward } from "@mui/icons-material";
import type {
  SystemRolesRoleItem1,
  SystemRolesList1,
} from "./shared/RpcModels";
import {
  fetchRoles,
  fetchUpsertRole,
  fetchDeleteRole,
} from "./rpc/system/roles";
import Notification from "./Notification";

const HIGH_BIT_MASK = (-(1n << 63n)).toString();

const maskToBit = (mask: bigint): number =>
  mask < 0n ? 63 : mask.toString(2).length - 1;

const bitToMask = (bit: number): string =>
  bit === 63 ? HIGH_BIT_MASK : (1n << BigInt(bit)).toString();

const nextMask = (roles: SystemRolesRoleItem1[]): string => {
  const bits = roles.map((r) => maskToBit(BigInt(r.mask)));
  const nextBit = bits.length === 0 ? 63 : Math.min(...bits) - 1;
  return bitToMask(nextBit < 0 ? 0 : nextBit);
};

const SystemRolesPage = (): JSX.Element => {
  const [items, setItems] = useState<SystemRolesRoleItem1[]>([]);
  const [newItem, setNewItem] = useState<SystemRolesRoleItem1>({
    name: "",
    mask: "",
    display: "",
  });
  const [notification, setNotification] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const handleNotificationClose = (): void => {
    setNotification(false);
  };

  const load = async (): Promise<void> => {
    try {
      const res: SystemRolesList1 = await fetchRoles();
      const sorted = res.roles.sort(
        (a, b) => maskToBit(BigInt(a.mask)) - maskToBit(BigInt(b.mask)),
      );
      setItems(sorted);
    } catch (e: any) {
      if (e?.response?.status === 403) {
        setForbidden(true);
      } else {
        setItems([]);
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

  const updateItem = async (
    index: number,
    field: keyof SystemRolesRoleItem1,
    value: string,
  ): Promise<void> => {
    const updated = [...items];
    (updated[index] as any)[field] = value;
    setItems(updated);
    await fetchUpsertRole(updated[index]);
    setNotification(true);
  };

  const handleDelete = async (name: string): Promise<void> => {
    await fetchDeleteRole({ name });
    void load();
    setNotification(true);
  };

  const handleAdd = async (): Promise<void> => {
    if (!newItem.name) return;
    await fetchUpsertRole({
      name: newItem.name,
      display: newItem.display,
      mask: nextMask(items),
    });
    setNewItem({ name: "", display: "", mask: "" });
    void load();
    setNotification(true);
  };

  const move = async (index: number, dir: number): Promise<void> => {
    const current = items[index];
    const bit = maskToBit(BigInt(current.mask));
    const targetBit = bit + dir;
    if (targetBit < 0 || targetBit > 63) return;
    const updated = [...items];
    const targetIdx = items.findIndex(
      (r) => maskToBit(BigInt(r.mask)) === targetBit,
    );
    const promises: Array<Promise<any>> = [];
    updated[index] = { ...current, mask: bitToMask(targetBit) };
    promises.push(fetchUpsertRole(updated[index]));
    if (targetIdx !== -1) {
      const other = items[targetIdx];
      updated[targetIdx] = { ...other, mask: current.mask };
      promises.push(fetchUpsertRole(updated[targetIdx]));
    }
    updated.sort(
      (a, b) => maskToBit(BigInt(a.mask)) - maskToBit(BigInt(b.mask)),
    );
    setItems(updated);
    await Promise.all(promises);
    setNotification(true);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5">System Roles</Typography>
      <Table size="small" sx={{ "& td, & th": { py: 0.5 } }}>
        <TableHead>
          <TableRow>
            <TableCell>Mask</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Display</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((i, idx) => {
            const bit = maskToBit(BigInt(i.mask));
            return (
              <TableRow key={i.name}>
                <TableCell>
                  <TextField value={i.mask} disabled />
                </TableCell>
                <TableCell>
                  <TextField
                    value={i.name}
                    onChange={(e) => updateItem(idx, "name", e.target.value)}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    value={i.display ?? ""}
                    onChange={(e) => updateItem(idx, "display", e.target.value)}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => void move(idx, -1)}
                    disabled={bit === 0}
                  >
                    <ArrowUpward />
                  </IconButton>
                  <IconButton
                    onClick={() => void move(idx, 1)}
                    disabled={bit === 63}
                  >
                    <ArrowDownward />
                  </IconButton>
                  <IconButton onClick={() => void handleDelete(i.name)}>
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            );
          })}
          <TableRow>
            <TableCell>
              <TextField value="" disabled />
            </TableCell>
            <TableCell>
              <TextField
                value={newItem.name}
                onChange={(e) =>
                  setNewItem({
                    ...newItem,
                    name: e.target.value,
                  })
                }
              />
            </TableCell>
            <TableCell>
              <TextField
                value={newItem.display ?? ""}
                onChange={(e) =>
                  setNewItem({
                    ...newItem,
                    display: e.target.value,
                  })
                }
              />
            </TableCell>
            <TableCell>
              <IconButton onClick={() => void handleAdd()}>
                <Add />
              </IconButton>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <Notification
        open={notification}
        handleClose={handleNotificationClose}
        severity="success"
        message="Saved"
      />
    </Box>
  );
};

export default SystemRolesPage;
