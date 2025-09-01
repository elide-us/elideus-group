import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton, LinearProgress, Stack, Typography } from '@mui/material';
import { PlayArrow, Pause, Replay } from '@mui/icons-material';

interface AudioPreviewProps {
    url: string;
}

const AudioPreview = ({ url }: AudioPreviewProps): JSX.Element => {
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [playing, setPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);

    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;
        const onTimeUpdate = (): void => {
            setCurrentTime(audio.currentTime);
            setProgress(audio.duration ? audio.currentTime / audio.duration : 0);
        };
        const onLoaded = (): void => {
            setDuration(audio.duration);
        };
        const onEnded = (): void => {
            setPlaying(false);
        };
        audio.addEventListener('timeupdate', onTimeUpdate);
        audio.addEventListener('loadedmetadata', onLoaded);
        audio.addEventListener('ended', onEnded);
        return () => {
            audio.removeEventListener('timeupdate', onTimeUpdate);
            audio.removeEventListener('loadedmetadata', onLoaded);
            audio.removeEventListener('ended', onEnded);
        };
    }, []);

    const togglePlay = (): void => {
        const audio = audioRef.current;
        if (!audio) return;
        if (playing) {
            audio.pause();
        } else {
            void audio.play();
        }
        setPlaying(!playing);
    };

    const restart = (): void => {
        const audio = audioRef.current;
        if (!audio) return;
        audio.currentTime = 0;
        if (!playing) {
            void audio.play();
            setPlaying(true);
        }
    };

    const format = (time: number): string => {
        const m = Math.floor(time / 60);
        const s = Math.floor(time % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    return (
        <Stack direction="row" spacing={1} alignItems="center">
            <audio ref={audioRef} src={url} />
            <IconButton size="small" onClick={togglePlay}>
                {playing ? <Pause /> : <PlayArrow />}
            </IconButton>
            <IconButton size="small" onClick={restart}>
                <Replay />
            </IconButton>
            <Box sx={{ width: 60 }}>
                <LinearProgress variant="determinate" value={progress * 100} />
            </Box>
            <Typography variant="caption">
                {format(currentTime)} / {format(duration)}
            </Typography>
        </Stack>
    );
};

export default AudioPreview;

