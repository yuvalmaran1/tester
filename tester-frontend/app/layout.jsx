import { Inter } from 'next/font/google';
import './globals.css';
import Sidebar from './components/NavBar';
import Providers from './components/Providers';
import { ConnectionProvider } from './contexts/ConnectionContext';

const inter = Inter({
    subsets: ['latin'],
    weight: ['300', '400', '500', '600', '700', '800'],
    display: 'swap',
});

export const metadata = {
    title: 'Test Framework',
    description: 'HiL Testing Framework',
    icons: {
        icon: '/icon.svg',
        shortcut: '/icon.svg',
        apple: '/icon.svg',
    },
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className={inter.className} style={{ backgroundColor: '#0d1117' }}>
                <Providers>
                    <ConnectionProvider>
                        <div className="flex h-screen overflow-hidden">
                            <Sidebar />
                            <div className="flex-1 overflow-y-auto min-w-0">
                                {children}
                            </div>
                        </div>
                    </ConnectionProvider>
                </Providers>
            </body>
        </html>
    );
}
