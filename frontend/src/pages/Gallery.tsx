import { useState, type JSX } from 'react';
import { Tabs, Tab, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageTitle from '../components/PageTitle';

const Gallery = (): JSX.Element => {
        const [value, setValue] = useState(0);
        const navigate = useNavigate();

        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const openProfile = (guid: string): void => {
                navigate(`/profile/${guid}`);
        };

        return (
                <div>
                        <PageTitle>Gallery</PageTitle>
                        <Tabs
                                value={value}
                                onChange={(_e, newValue) => setValue(newValue)}
                                aria-label="gallery filters"
                        >
                                <Tab label="Image" />
                                <Tab label="Video" />
                                <Tab label="Audio" />
                                <Tab label="Document" />
                                <Tab label="Misc" />
                        </Tabs>
                        <Typography>Coming soon...</Typography>
                </div>
        );
};

export default Gallery;
