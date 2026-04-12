import type { ComponentType } from 'react';

import { ContentPanel } from '../components/ContentPanel';
import { HamburgerToggle } from '../components/HamburgerToggle';
import { ImageElement } from '../components/ImageElement';
import { LabelElement } from '../components/LabelElement';
import { LinkButton } from '../components/LinkButton';
import { NavigationSidebar } from '../components/NavigationSidebar';
import { SidebarContent } from '../components/SidebarContent';
import { SidebarFooter } from '../components/SidebarFooter';
import { SidebarHeader } from '../components/SidebarHeader';
import { SimplePage } from '../components/SimplePage';
import { StringControl } from '../components/StringControl';
import { Workbench } from '../components/Workbench';

import type { CmsComponentProps } from './types';

export const COMPONENT_REGISTRY: Record<string, ComponentType<CmsComponentProps>> = {
	Workbench,
	NavigationSidebar,
	SidebarHeader,
	SidebarContent,
	SidebarFooter,
	HamburgerToggle,
	ContentPanel,
	SimplePage,
	ImageElement,
	LinkButton,
	LabelElement,
	StringControl,
};
