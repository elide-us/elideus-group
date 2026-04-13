import type { ComponentType } from 'react';

import { DevModeToggle } from '../components/DevModeToggle';
import { DatabaseBuilder } from '../components/DatabaseBuilder';
import { ContentPanel } from '../components/ContentPanel';
import { ComponentBuilder } from '../components/ComponentBuilder';
import { HamburgerToggle } from '../components/HamburgerToggle';
import { ImageElement } from '../components/ImageElement';
import { LabelElement } from '../components/LabelElement';
import { LoginControl } from '../components/LoginControl';
import { LinkButton } from '../components/LinkButton';
import { NavigationTreeView } from '../components/NavigationTreeView';
import { ObjectEditor } from '../components/ObjectEditor';
import { ObjectTreeView } from '../components/ObjectTreeView';
import { ModulesBuilder } from '../components/ModulesBuilder';
import { NavigationSidebar } from '../components/NavigationSidebar';
import { SidebarContent } from '../components/SidebarContent';
import { SidebarFooter } from '../components/SidebarFooter';
import { SidebarHeader } from '../components/SidebarHeader';
import { SimplePage } from '../components/SimplePage';
import { StringControl } from '../components/StringControl';
import { TypesBuilder } from '../components/TypesBuilder';
import { UserProfileControl } from '../components/UserProfileControl';
import { Workbench } from '../components/Workbench';

import type { CmsComponentProps } from './types';

export const COMPONENT_REGISTRY: Record<string, ComponentType<CmsComponentProps>> = {
	Workbench,
	NavigationSidebar,
	SidebarHeader,
	SidebarContent,
	SidebarFooter,
	DevModeToggle,
	HamburgerToggle,
	NavigationTreeView,
	ObjectTreeView,
	ContentPanel,
	SimplePage,
	ObjectEditor,
	ImageElement,
	LinkButton,
	LabelElement,
	LoginControl,
	UserProfileControl,
	StringControl,
	DatabaseBuilder: DatabaseBuilder as unknown as ComponentType<CmsComponentProps>,
	TypesBuilder: TypesBuilder as unknown as ComponentType<CmsComponentProps>,
	ModulesBuilder: ModulesBuilder as unknown as ComponentType<CmsComponentProps>,
	ComponentBuilder: ComponentBuilder as unknown as ComponentType<CmsComponentProps>,
};
