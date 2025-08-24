import { useEffect, useState } from "react";
import {
  Box,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  IconButton,
  Typography,
} from "@mui/material";
import TextField from "@mui/material/TextField";
import { Delete, Add, ArrowUpward, ArrowDownward } from "@mui/icons-material";
import EditBox from "./EditBox";
import type {
  SystemRolesRoleItem1,
  SystemRolesList1,
} from "./shared/RpcModels";
import {
  fetchRoles,
  fetchUpsertRole,
  fetchDeleteRole
} from "./rpc/system/roles";
import Notification from "./Notification";

const HIGH_BIT_MASK = (-(1n << 63n)).toString();

const maskToBit = (mask: bigint): number =>
  mask < 0n ? 63 : mask.toString(2).length - 1;

const bitToMask = (bit: number): string =>
  bit === 63 ? HIGH_BIT_MASK : (1n << BigInt(bit)).toString();

const nextMask = (roles: SystemRolesRoleItem1[]): string => {
  const used = new Set(roles.map((r) => maskToBit(BigInt(r.mask))));
  for (let bit = 0; bit < 64; bit++) {
    if (!used.has(bit)) return bitToMask(bit);
  }
  return bitToMask(0);
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
            <TableCell sx={{ width: '20%' }}>Mask</TableCell>
            <TableCell sx={{ width: '25%' }}>Name</TableCell>
            <TableCell sx={{ width: '25%' }}>Display</TableCell>
            <TableCell sx={{ width: '10%' }} />
            <TableCell sx={{ width: '10%' }} />
            <TableCell sx={{ width: '10%' }} />
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((i, idx) => {
            const bit = maskToBit(BigInt(i.mask));
            return (
              <TableRow key={i.name}>
                <TableCell sx={{ width: '20%' }}>
                  <TextField sx={{ width: '100%' }} value={i.mask} disabled />
                </TableCell>
                <TableCell sx={{ width: '25%' }}>
                  <EditBox
                    width="100%"
                    value={i.name}
                    onCommit={(val) => updateItem(idx, 'name', String(val))}
                  />
                </TableCell>
                <TableCell sx={{ width: '25%' }}>
                  <EditBox
                    width="100%"
                    value={i.display ?? ''}
                    onCommit={(val) => updateItem(idx, 'display', String(val))}
                  />
                </TableCell>
                <TableCell sx={{ width: '10%' }}>
                  <IconButton
                    onClick={() => void move(idx, -1)}
                    disabled={bit === 0}
                  >
                    <ArrowUpward />
                  </IconButton>
                </TableCell>
                <TableCell sx={{ width: '10%' }}>
                  <IconButton
                    onClick={() => void move(idx, 1)}
                    disabled={bit === 63}
                  >
                    <ArrowDownward />
                  </IconButton>
                </TableCell>
                <TableCell sx={{ width: '10%' }}>
                  <IconButton onClick={() => void handleDelete(i.name)}>
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            );
          })}
          <TableRow>
            <TableCell sx={{ width: '20%' }}>
              <TextField sx={{ width: '100%' }} value="" disabled />
            </TableCell>
            <TableCell sx={{ width: '25%' }}>
              <TextField
                sx={{ width: '100%' }}
                value={newItem.name}
                onChange={(e) =>
                  setNewItem({
                    ...newItem,
                    name: e.target.value,
                  })
                }
              />
            </TableCell>
            <TableCell sx={{ width: '25%' }}>
              <TextField
                sx={{ width: '100%' }}
                value={newItem.display ?? ''}
                onChange={(e) =>
                  setNewItem({
                    ...newItem,
                    display: e.target.value,
                  })
                }
              />
            </TableCell>
            <TableCell sx={{ width: '10%' }} />
            <TableCell sx={{ width: '10%' }} />
            <TableCell sx={{ width: '10%' }}>
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
