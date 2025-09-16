import { useEffect, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent, MouseEvent } from 'react';
import { Button, TextField } from '@mui/material';

type DisplayMode = 'display' | 'armed' | 'editing';

interface StorageItemNameProps {
    name: string;
    allowRename?: boolean;
    onRename: (newName: string) => Promise<void>;
}

const StorageItemName = ({ name, allowRename = true, onRename }: StorageItemNameProps): JSX.Element => {
    const [mode, setMode] = useState<DisplayMode>('display');
    const [value, setValue] = useState(name);
    const [pending, setPending] = useState(false);
    const [errorText, setErrorText] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement | null>(null);
    const cancelNextBlur = useRef(false);

    useEffect(() => {
        setMode('display');
        setValue(name);
        setPending(false);
        setErrorText(null);
    }, [name]);

    useEffect(() => {
        if (mode === 'editing' && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [mode]);

    const canEdit = useMemo(() => allowRename && !pending, [allowRename, pending]);

    const handleActivate = (event: MouseEvent | KeyboardEvent): void => {
        event.stopPropagation();
        if (!canEdit) return;
        setMode('armed');
    };

    const handleStartEditing = (event: MouseEvent | KeyboardEvent): void => {
        event.stopPropagation();
        if (!canEdit) return;
        setMode('editing');
    };

    const resetState = (): void => {
        setMode('display');
        setValue(name);
        setErrorText(null);
        setPending(false);
    };

    const commitRename = async (nextValue: string): Promise<void> => {
        if (!canEdit) return;
        const trimmed = nextValue.trim();
        if (!trimmed || trimmed === name) {
            resetState();
            return;
        }
        setPending(true);
        try {
            await onRename(trimmed);
            setValue(trimmed);
            setMode('display');
            setErrorText(null);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Unable to rename item';
            setErrorText(message);
            setMode('editing');
            if (inputRef.current) {
                inputRef.current.focus();
            }
            return;
        } finally {
            setPending(false);
        }
    };

    const handleBlur = async (): Promise<void> => {
        if (cancelNextBlur.current) {
            cancelNextBlur.current = false;
            return;
        }
        if (mode === 'armed') {
            setMode('display');
            return;
        }
        if (mode === 'editing') {
            await commitRename(value);
        }
    };

    const handleKeyDown = async (event: KeyboardEvent<HTMLInputElement>): Promise<void> => {
        if (event.key === 'Enter') {
            event.preventDefault();
            await commitRename(value);
        } else if (event.key === 'Escape') {
            event.preventDefault();
            cancelNextBlur.current = true;
            resetState();
        }
    };

    if (!allowRename) {
        return <span>{name}</span>;
    }

    if (mode === 'armed') {
        return (
            <Button
                size="small"
                variant="text"
                onClick={handleStartEditing}
                onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        void handleStartEditing(event);
                    }
                }}
                onBlur={() => {
                    cancelNextBlur.current = false;
                    setMode('display');
                }}
            >
                {name}
            </Button>
        );
    }

    if (mode === 'editing') {
        return (
            <TextField
                size="small"
                inputRef={inputRef}
                value={value}
                onChange={(event) => setValue(event.target.value)}
                onBlur={() => {
                    void handleBlur();
                }}
                onClick={(event) => event.stopPropagation()}
                onKeyDown={handleKeyDown}
                error={Boolean(errorText)}
                helperText={errorText ?? undefined}
                disabled={pending}
                inputProps={{ 'aria-label': 'Rename storage item' }}
            />
        );
    }

    return (
        <span
            onClick={handleActivate}
            onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    handleActivate(event);
                }
            }}
            role="button"
            tabIndex={0}
        >
            {name}
        </span>
    );
};

export default StorageItemName;
