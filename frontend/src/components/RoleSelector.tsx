import { useState } from "react";
import {
        Stack,
        List,
        ListItemButton,
        ListItemText,
        IconButton,
} from "@mui/material";
import { ArrowForwardIos, ArrowBackIos } from "@mui/icons-material";

interface RoleSelectorProps {
        available: string[];
        selected: string[];
        onAdd: (role: string) => void;
        onRemove: (role: string) => void;
}

const MAX_HEIGHT = 120;

const RoleSelector = ({ available, selected, onAdd, onRemove }: RoleSelectorProps): JSX.Element => {
        const [left, setLeft] = useState<string | null>(null);
        const [right, setRight] = useState<string | null>(null);

        const handleAdd = (): void => {
                if (!left) return;
                onAdd(left);
                setLeft(null);
        };

        const handleRemove = (): void => {
                if (!right) return;
                onRemove(right);
                setRight(null);
        };

        return (
                <Stack direction="row" spacing={1}>
                        <List
                                sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: "auto", border: 1 }}
                        >
                                {available.map((role) => (
                                        <ListItemButton
                                                key={role}
                                                selected={left === role}
                                                onClick={() => setLeft(role)}
                                        >
                                                <ListItemText primary={role} />
                                        </ListItemButton>
                                ))}
                        </List>
                        <Stack spacing={1} justifyContent="center">
                                <IconButton onClick={handleAdd}>
                                        <ArrowForwardIos />
                                </IconButton>
                                <IconButton onClick={handleRemove}>
                                        <ArrowBackIos />
                                </IconButton>
                        </Stack>
                        <List
                                sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: "auto", border: 1 }}
                        >
                                {selected.map((role) => (
                                        <ListItemButton
                                                key={role}
                                                selected={right === role}
                                                onClick={() => setRight(role)}
                                        >
                                                <ListItemText primary={role} />
                                        </ListItemButton>
                                ))}
                        </List>
                </Stack>
        );
};

export default RoleSelector;
