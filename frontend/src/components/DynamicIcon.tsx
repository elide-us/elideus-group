import { memo } from 'react';
import * as MuiIcons from '@mui/icons-material';

interface DynamicIconProps {
  name: string | null | undefined;
}

const DynamicIcon = memo(({ name }: DynamicIconProps): JSX.Element => {
  const IconComponent = name
    ? (MuiIcons as Record<string, typeof MuiIcons.Adjust>)[name] ?? MuiIcons.Adjust
    : MuiIcons.Adjust;

  return <IconComponent />;
});

DynamicIcon.displayName = 'DynamicIcon';

export default DynamicIcon;
