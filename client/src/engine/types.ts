export interface PathNode {
	guid: string;
	component: string;
	category: string;
	label: string | null;
	fieldBinding: string | null;
	sequence: number;
	children: PathNode[];
}

export interface CmsComponentProps {
	node: PathNode;
	data: Record<string, unknown>;
	children?: React.ReactNode;
}
