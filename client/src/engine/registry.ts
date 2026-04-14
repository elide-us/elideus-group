import type { ComponentType } from 'react';

import { BoolToggle } from '../components/BoolToggle';
import { ButtonLinkControl } from '../components/ButtonLinkControl';
import { CollapsibleSection } from '../components/CollapsibleSection';
import { ComponentBuilder } from '../components/ComponentBuilder';
import { ContentPanel } from '../components/ContentPanel';
import { DatabaseBuilder } from '../components/DatabaseBuilder';
import { DevModeToggle } from '../components/DevModeToggle';
import { HamburgerToggle } from '../components/HamburgerToggle';
import { ImageElement } from '../components/ImageElement';
import { IntControl } from '../components/IntControl';
import { LabelElement } from '../components/LabelElement';
import { LinkButton } from '../components/LinkButton';
import { LoginControl } from '../components/LoginControl';
import { ModulesBuilder } from '../components/ModulesBuilder';
import { NavigationItem } from '../components/NavigationItem';
import { NavigationSidebar } from '../components/NavigationSidebar';
import { NavigationTreeView } from '../components/NavigationTreeView';
import { ObjectEditor } from '../components/ObjectEditor';
import { ObjectTreeNode } from '../components/ObjectTreeNode';
import { ObjectTreeView } from '../components/ObjectTreeView';
import { ReadOnlyDisplay } from '../components/ReadOnlyDisplay';
import { SidebarContent } from '../components/SidebarContent';
import { SidebarFooter } from '../components/SidebarFooter';
import { SidebarHeader } from '../components/SidebarHeader';
import { SimplePage } from '../components/SimplePage';
import { StringControl } from '../components/StringControl';
import { TypesBuilder } from '../components/TypesBuilder';
import { UserProfileControl } from '../components/UserProfileControl';
import { Workbench } from '../components/Workbench';
import {
	ComponentPreview,
	ComponentTreePanel,
	ContractPanel,
	PropertyPanel,
	QueryPreviewPanel,
} from '../components/builder';

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
	BoolToggle,
	ButtonLinkControl,
	CollapsibleSection,
	IntControl,
	NavigationItem,
	ObjectTreeNode,
	ReadOnlyDisplay,
	DatabaseBuilder: DatabaseBuilder as unknown as ComponentType<CmsComponentProps>,
	TypesBuilder: TypesBuilder as unknown as ComponentType<CmsComponentProps>,
	ModulesBuilder: ModulesBuilder as unknown as ComponentType<CmsComponentProps>,
	ComponentBuilder: ComponentBuilder as unknown as ComponentType<CmsComponentProps>,
	ComponentPreview: ComponentPreview as unknown as ComponentType<CmsComponentProps>,
	ComponentTreePanel: ComponentTreePanel as unknown as ComponentType<CmsComponentProps>,
	ContractPanel: ContractPanel as unknown as ComponentType<CmsComponentProps>,
	PropertyPanel: PropertyPanel as unknown as ComponentType<CmsComponentProps>,
	QueryPreviewPanel: QueryPreviewPanel as unknown as ComponentType<CmsComponentProps>,
};
