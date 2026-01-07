import { useState } from 'react';
import { RefreshCw, MessageSquare, Menu, BookOpen, Settings } from 'lucide-react';

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    onNewChat: () => void;
}

export function Sidebar({ isOpen, setIsOpen, onNewChat }: SidebarProps) {
    return (
        <div
            className={`
        ${isOpen ? 'w-64' : 'w-16'} 
        bg-gray-950 border-r border-gray-800 transition-all duration-300 ease-in-out
        flex flex-col shrink-0 overflow-hidden
      `}
        >
            {/* Header / Toggle */}
            <div className="h-16 flex items-center px-4 border-b border-gray-800">
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors"
                >
                    <Menu size={20} />
                </button>
                {isOpen && (
                    <span className="ml-3 font-semibold text-gray-200 fade-in whitespace-nowrap">
                        Obsidian AI
                    </span>
                )}
            </div>

            {/* New Chat Button */}
            <div className="p-4">
                <button
                    onClick={onNewChat}
                    className={`
            flex items-center gap-3 bg-gray-800 hover:bg-gray-700 
            text-gray-200 px-4 py-3 rounded-xl transition-all w-full
            border border-gray-700 shadow-sm
            ${!isOpen ? 'justify-center px-0' : ''}
          `}
                >
                    <RefreshCw size={20} className={!isOpen ? "ml-1" : ""} />
                    {isOpen && <span className="font-medium whitespace-nowrap">New Chat</span>}
                </button>
            </div>

            {/* Navigation (Stubbed) */}
            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
                {/* Recent Section */}
                {isOpen && (
                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Recent
                    </div>
                )}

                {/* Example Item */}
                <button
                    onClick={() => alert("This is a placeholder. History feature coming soon!")}
                    className={`
          w-full flex items-center gap-3 px-3 py-2 rounded-lg 
          text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors
          ${!isOpen ? 'justify-center' : ''}
        `}>
                    <MessageSquare size={18} />
                    {isOpen && <span className="truncate text-sm">Example Chat (Stub)</span>}
                </button>
            </div>

            {/* Footer / Settings */}
            <div className="p-4 border-t border-gray-800 space-y-2">
                <button className={`
          w-full flex items-center gap-3 px-3 py-2 rounded-lg 
          text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors
          ${!isOpen ? 'justify-center' : ''}
        `}>
                    <BookOpen size={18} />
                    {isOpen && <span className="truncate text-sm">Help & FAQ</span>}
                </button>
                <button className={`
          w-full flex items-center gap-3 px-3 py-2 rounded-lg 
          text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors
          ${!isOpen ? 'justify-center' : ''}
        `}>
                    <Settings size={18} />
                    {isOpen && <span className="truncate text-sm">Settings</span>}
                </button>
            </div>
        </div>
    );
}
