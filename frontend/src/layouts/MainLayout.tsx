import { ReactNode } from 'react';

interface MainLayoutProps {
    children: ReactNode;
    sidebar: ReactNode;
}

export function MainLayout({ children, sidebar }: MainLayoutProps) {
    return (
        <div className="flex h-screen w-screen bg-gray-900 text-gray-100 overflow-hidden">
            {sidebar}

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col relative w-full h-full">
                {children}
            </main>
        </div>
    );
}
