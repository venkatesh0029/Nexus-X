import React, { useEffect } from 'react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  {
    id: 'user',
    position: { x: 350, y: 0 },
    data: { label: 'User Request' },
    style: {
        background: '#1f2937', 
        color: '#f9fafb', 
        border: '1px solid #374151',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center'
    },
  },
  {
    id: 'supervisor',
    position: { x: 350, y: 100 },
    data: { label: 'Supervisor' },
    style: {
        background: '#9333ea', // Purple for the brain
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
  {
    id: 'system_agent',
    position: { x: 150, y: 200 },
    data: { label: 'System Agent' },
    style: {
        background: '#2563eb', // Blue
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
  {
    id: 'vision_agent',
    position: { x: 550, y: 200 },
    data: { label: 'Vision Agent' },
    style: {
        background: '#ec4899', // Pink
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
  {
    id: 'tools',
    position: { x: 150, y: 350 },
    data: { label: 'Tools Layer' },
    style: {
        background: '#ea580c', 
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
  {
    id: 'security',
    position: { x: 350, y: 350 },
    data: { label: 'Security Gateway' },
    style: {
        background: '#dc2626', 
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
  {
    id: 'memory',
    position: { x: 550, y: 350 },
    data: { label: 'Vector Memory' },
    style: {
        background: '#16a34a', 
        color: 'white', 
        border: 'none',
        borderRadius: '8px',
        width: 150,
        fontWeight: 'bold',
        textAlign: 'center',
        transition: 'all 0.3s ease'
    },
  },
];

const initialEdges = [
  { id: 'e-user-super', source: 'user', target: 'supervisor', animated: true },
  
  // Routing paths
  { id: 'e-super-system', source: 'supervisor', target: 'system_agent', animated: true, type: 'smoothstep' },
  { id: 'e-super-vision', source: 'supervisor', target: 'vision_agent', animated: true, type: 'smoothstep' },
  
  // System Agent logic
  { id: 'e-sys-tools', source: 'system_agent', target: 'tools', animated: true },
  { id: 'e-sys-security', source: 'system_agent', target: 'security', animated: true },
  { id: 'e-security-tools', source: 'security', target: 'tools', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  
  // Vision Agent tools
  { id: 'e-vis-tools', source: 'vision_agent', target: 'tools', animated: true },
  
  // Global tools hit memory
  { id: 'e-tools-memory', source: 'tools', target: 'memory', animated: true },
  { id: 'e-sys-memory', source: 'system_agent', target: 'memory', animated: true, type: 'smoothstep' },
];

const defaultEdgeOptions = {
    style: { strokeWidth: 2, stroke: '#9ca3af' },
    animated: true,
};

export default function LangGraphVisualizer({ activeNode }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    // Pulse animation logic
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === activeNode) {
          return {
            ...node,
            style: {
              ...node.style,
              boxShadow: '0 0 15px 5px rgba(59, 130, 246, 0.5)',
              transform: 'scale(1.05)',
              filter: 'brightness(1.2)',
              zIndex: 10
            },
          };
        }
        return {
          ...node,
          style: {
            ...initialNodes.find(n => n.id === node.id).style,
            opacity: activeNode ? 0.6 : 1, // Dim inactive nodes
            zIndex: 1
          },
        };
      })
    );
  }, [activeNode, setNodes]);

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '500px' }} className="bg-gray-50 border rounded-lg shadow-inner">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      />
    </div>
  );
}
