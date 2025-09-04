import { useState, type JSX } from 'react';
import { Tabs, Tab, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';

const Gallery = (): JSX.Element => {
        const [value, setValue] = useState(0);

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
