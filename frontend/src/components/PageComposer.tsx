import { ComponentTreePanel, type ComponentTreePanelProps } from './builder/ComponentTreePanel';

export function PageComposer(props: ComponentTreePanelProps): JSX.Element {
	return <ComponentTreePanel {...props} />;
}

export default PageComposer;
