import type { ElementType } from 'react';
import {
    Home as HomeIcon,
    Folder as FolderIcon,
    SmartToy as SmartToyIcon,
    Diamond as DiamondIcon,
    PhotoLibrary as PhotoLibraryIcon,
    Pets as PetsIcon,
    Key as KeyIcon,
    Adjust as AdjustIcon,
    Menu as MenuIcon,
    PeopleOutline as PeopleOutlineIcon,
    AssignmentInd as AssignmentIndIcon,
    PermDataSetting as PermDataSettingIcon,
} from '@mui/icons-material';

export const iconMap: Record<string, ElementType> = {
    home: HomeIcon,
    folder: FolderIcon,
    smartToy: SmartToyIcon,
    diamond: DiamondIcon,
    photoLibrary: PhotoLibraryIcon,
    pets: PetsIcon,
    key: KeyIcon,
    menu: MenuIcon,
    users: PeopleOutlineIcon,
    roles: AssignmentIndIcon,
    config: PermDataSettingIcon,
};

export const defaultIcon = AdjustIcon;
