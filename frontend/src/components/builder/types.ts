export type ComponentCategory = 'page' | 'section' | 'control';

export interface ComponentDefinition {
	guid: string;
	name: string;
	category: ComponentCategory;
	refDefaultTypeGuid?: string | null;
	defaultTypeName?: string | null;
}

export interface ComponentTreeNode {
	guid: string;
	parentGuid: string | null;
	componentGuid: string;
	componentName: string;
	category: ComponentCategory;
	sequence: number;
	pubLabel?: string;
	fieldBinding?: string;
	rpcOperation?: string;
	rpcContract?: string;
	children: ComponentTreeNode[];
}

export interface DataBindingRow {
	guid: string;
	sourceType: string;
	alias: string;
	value: string;
}

export interface TreeMoveRequest {
	nodeGuid: string;
	newParentGuid: string | null;
	newSequence: number;
}
