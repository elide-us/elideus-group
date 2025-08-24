import React, { useState, useEffect } from 'react';
import TextField from '@mui/material/TextField';
import Notification from './Notification';

interface EditBoxProps {
		value: string | number;
		onCommit: (value: string | number) => Promise<void> | void;
		width?: string | number;
}

const EditBox = ({ value, onCommit, width = '100%' }: EditBoxProps): JSX.Element => {
		const [internal, setInternal] = useState<string | number>(value);
		const [notify, setNotify] = useState(false);

		useEffect(() => {
				setInternal(value);
		}, [value]);

		const commit = async (): Promise<void> => {
				if (internal !== value) {
						await onCommit(internal);
						setNotify(true);
				}
		};

		const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
				if (e.key === 'Enter' || e.key === 'Tab') {
						void commit();
				}
		};

		const handleBlur = (): void => {
				void commit();
		};

		const handleClose = (): void => {
				setNotify(false);
		};

		const type = typeof value === 'number' ? 'number' : 'text';

		return (
				<>
						<TextField
								sx={{ width }}
								type={type}
								value={internal}
								onChange={(e) => {
										const target = e.target as HTMLInputElement;
										const val = type === 'number' ? Number(target.value) : target.value;
										setInternal(val);
								}}
								onKeyDown={handleKeyDown}
								onBlur={handleBlur}
						/>
						<Notification
								open={notify}
								handleClose={handleClose}
								severity='success'
								message='Saved'
						/>
				</>
		);

};

export default EditBox;
