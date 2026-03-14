import React, { useState } from 'react';

const CommandApproval = ({ pendingApprovals = [], onApprove, onReject, onBatchApprove }) => {
    const [expandedIds, setExpandedIds] = useState({});

    const toggleExpand = (id) => {
        setExpandedIds(prev => ({ ...prev, [id]: !prev[id] }));
    };

    if (!pendingApprovals || pendingApprovals.length === 0) {
        return (
             <div className="text-center text-gray-400 text-sm">
                 No pending operations.
             </div>
        );
    }

    const getRiskColor = (riskLevel) => {
        switch (riskLevel?.toLowerCase()) {
            case 'high': return 'bg-red-50 text-red-700 border-red-200';
            case 'medium': return 'bg-yellow-50 text-yellow-800 border-yellow-200';
            case 'low': return 'bg-gray-50 text-gray-700 border-gray-200';
            default: return 'bg-blue-50 text-blue-700 border-blue-200';
        }
    };

    return (
        <div className="flex flex-col gap-4 max-h-[400px] overflow-y-auto pr-2">
            
            {pendingApprovals.length > 1 && (
                <div className="flex justify-between items-center mb-2 pb-2 border-b">
                     <span className="text-sm font-semibold text-gray-700">{pendingApprovals.length} Pending Actions</span>
                     <button
                        onClick={onBatchApprove}
                        className="py-1 px-3 bg-indigo-600 text-white rounded text-xs font-semibold hover:bg-indigo-700 transition"
                     >
                         Batch Approve All
                     </button>
                </div>
            )}

            {pendingApprovals.map((req, index) => {
                const isExpanded = expandedIds[req.id] || false;
                const riskColorList = getRiskColor(req.riskLevel);

                return (
                    <div key={req.id || index} className={`flex flex-col gap-2 p-3 rounded-md border shadow-sm ${riskColorList}`}>
                        <div className="flex justify-between items-start">
                            <div className="flex flex-col">
                                <span className="font-semibold text-sm">Action Requirement: {req.action || 'Execute'}</span>
                                <span className="text-xs opacity-80">Risk Level: {req.riskLevel || 'Unknown'}</span>
                            </div>
                            <button onClick={() => toggleExpand(req.id)} className="text-xs underline hover:opacity-80">
                                {isExpanded ? 'Hide Details' : 'View Payload'}
                            </button>
                        </div>

                        {isExpanded ? (
                             <div className="bg-white/50 p-2 rounded text-xs font-mono overflow-x-auto border border-white/40 shadow-inner break-all">
                                {req.command}
                             </div>
                        ) : (
                             <div className="truncate bg-white/50 p-2 rounded text-xs font-mono border border-white/40 shadow-inner">
                                {req.command}
                             </div>
                        )}

                        <div className="flex gap-2 mt-2">
                            <button
                                onClick={() => onReject(req.id)}
                                className="flex-1 py-1.5 px-3 bg-white border border-gray-300 text-gray-700 rounded shadow-sm hover:bg-gray-50 transition-colors text-xs font-medium"
                            >
                                Reject
                            </button>
                            <button
                                onClick={() => onApprove(req.id)}
                                className="flex-1 py-1.5 px-3 bg-green-600 text-white rounded shadow-sm hover:bg-green-700 transition-colors text-xs font-medium"
                            >
                                Approve
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default CommandApproval;
