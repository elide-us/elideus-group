import { useState } from "react";
import {
	Stack,
	List,
	ListItemButton,
	ListItemText,
	IconButton,
} from "@mui/material";
import { ArrowForwardIos, ArrowBackIos } from "@mui/icons-material";

interface RolesSelectorProps {
	allRoles: string[];
	value: string[];
	onChange: (roles: string[]) => void;
	maxHeight?: number;
}

const RolesSelector = ({
	allRoles,
	value,
	onChange,
	maxHeight = 120,
}: RolesSelectorProps): JSX.Element => {
	const [left, setLeft] = useState<string | null>(null);
	const [right, setRight] = useState<string | null>(null);
	const available = allRoles.filter((r) => !value.includes(r));
	const moveRight = (): void => {
		if (!left) return;
		onChange([...value, left]);
		setLeft(null);
	};
	const moveLeft = (): void => {
		if (!right) return;
		onChange(value.filter((r) => r !== right));
		setRight(null);
	};
        return (
                <Stack direction="row" spacing={1} sx={{ width: "100%" }}>
                        <List
                                sx={{
                                        flex: 1,
                                        minWidth: 200,
                                        maxHeight,
                                        overflow: "auto",
                                        border: 1,
                                }}
                        >
				{available.map((role) => (
					<ListItemButton
						key={role}
						selected={left === role}
						onClick={() => setLeft(role)}
					>
						<ListItemText
							primary={role}
							primaryTypographyProps={{
								fontFamily: "monospace",
								variant: "body2",
							}}
						/>
					</ListItemButton>
				))}
			</List>
			<Stack spacing={1} justifyContent="center">
				<IconButton onClick={moveRight}>
					<ArrowForwardIos />
				</IconButton>
				<IconButton onClick={moveLeft}>
					<ArrowBackIos />
				</IconButton>
			</Stack>
                        <List
                                sx={{
                                        flex: 1,
                                        minWidth: 200,
                                        maxHeight,
                                        overflow: "auto",
                                        border: 1,
                                }}
                        >
				{value.map((role) => (
					<ListItemButton
						key={role}
						selected={right === role}
						onClick={() => setRight(role)}
					>
						<ListItemText
							primary={role}
							primaryTypographyProps={{
								fontFamily: "monospace",
								variant: "body2",
							}}
						/>
					</ListItemButton>
				))}
			</List>
		</Stack>
	);
};

export default RolesSelector;

