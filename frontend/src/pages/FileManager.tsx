import { useContext } from "react";
import { Box, Typography } from "@mui/material";
import UserContext from "../shared/UserContext";

const FileManager = (): JSX.Element => {
    useContext(UserContext);
    return (
        <Box sx={{ py: 4, textAlign: "center" }}>
            <Typography variant="h4">File Manager coming soon</Typography>
        </Box>
    );
};

export default FileManager;

