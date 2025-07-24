import { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import TextField from '@mui/material/TextField';
import Notification from './Notification';

interface EditBoxProps {
    label?: string;
    value: string | number;
    type?: string;
    onCommit: (value: string | number) => Promise<void> | void;
    manual?: boolean;
    [key: string]: any;
}

export interface EditBoxHandle {
    commit: () => Promise<void>;
}

const EditBox = forwardRef<EditBoxHandle, EditBoxProps>(({ label, value, type = 'text', onCommit, manual = false, ...rest }, ref) => {
    const [internal, setInternal] = useState<string | number>(value);
    const [notify, setNotify] = useState(false);

    useEffect(() => { setInternal(value); }, [value]);

    const commit = async (): Promise<void> => {
        if (internal !== value) {
            await onCommit(internal);
            setNotify(true);
        }
    };

    useImperativeHandle(ref, () => ({ commit }));

    const handleKeyDown = (e: React.KeyboardEvent): void => {
        if (!manual && (e.key === 'Enter' || e.key === 'Tab')) {
            void commit();
        }
    };

    const handleBlur = (): void => { if (!manual) void commit(); };

    const handleClose = (): void => { setNotify(false); };

    return (
        <>
            <TextField
                label={label}
                type={type}
                value={internal}
                onChange={e => setInternal(type === 'number' ? Number((e.target as HTMLInputElement).value) : (e.target as HTMLInputElement).value)}
                onKeyDown={handleKeyDown}
                onBlur={handleBlur}
                {...rest}
            />
            <Notification
                open={notify}
                handleClose={handleClose}
                severity='success'
                message='Saved'
            />
        </>
    );
});

export default EditBox;
