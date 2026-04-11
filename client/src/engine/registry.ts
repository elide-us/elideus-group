import type { ComponentType } from 'react';

import { ContentPanel } from '../components/ContentPanel';
import { ImageElement } from '../components/ImageElement';
import { LabelElement } from '../components/LabelElement';
import { LinkButton } from '../components/LinkButton';
import { SimplePage } from '../components/SimplePage';
import { StringControl } from '../components/StringControl';
import { Workbench } from '../components/Workbench';

import type { CmsComponentProps } from './types';

export const COMPONENT_REGISTRY: Record<string, ComponentType<CmsComponentProps>> = {
	Workbench,
	ContentPanel,
	SimplePage,
	ImageElement,
	LinkButton,
	LabelElement,
	StringControl,
};
