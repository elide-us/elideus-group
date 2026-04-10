import type { ComponentType } from 'react';

import { ContentPanel } from '../components/ContentPanel';
import { StringControl } from '../components/StringControl';
import { Workbench } from '../components/Workbench';

import type { CmsComponentProps } from './types';

export const COMPONENT_REGISTRY: Record<string, ComponentType<CmsComponentProps>> = {
	Workbench,
	ContentPanel,
	StringControl,
};
