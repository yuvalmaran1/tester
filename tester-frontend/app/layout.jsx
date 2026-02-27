import { Inter } from 'next/font/google';
import './globals.css';
// components
import Navbar from './components/Navbar';
import { ConnectionProvider } from './contexts/ConnectionContext';

const inter = Inter({
    subsets: ['latin'],
    weight: ['300', '400', '500', '600', '700', '800'],
    display: 'swap'
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
            <body className={inter.className}>
                <ConnectionProvider>
                    <Navbar />
                    {children}
                </ConnectionProvider>
            </body>
        </html>
    );
}
