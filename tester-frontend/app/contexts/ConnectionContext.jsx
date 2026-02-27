'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import { socket } from '../socket';

const ConnectionContext = createContext();

export const useConnection = () => {
    const context = useContext(ConnectionContext);
    if (!context) {
        throw new Error('useConnection must be used within a ConnectionProvider');
    }
    return context;
};

export const ConnectionProvider = ({ children }) => {
    const [connected, setConnected] = useState(false);
    const [connecting, setConnecting] = useState(true);

    useEffect(() => {
        // Check initial connection state
        const checkInitialState = () => {
            console.log('Checking initial socket state:', socket.connected);
            if (socket.connected) {
                console.log('Socket already connected on initialization');
                setConnected(true);
                setConnecting(false);
            } else {
                console.log('Socket not connected on initialization');
                setConnected(false);
                setConnecting(true);
            }
        };

        // Check immediately
        checkInitialState();

        // Also check after a short delay to handle any race conditions
        const timeoutId = setTimeout(checkInitialState, 100);

        const handleConnect = () => {
            console.log('Socket connected');
            setConnected(true);
            setConnecting(false);
        };

        const handleDisconnect = () => {
            console.log('Socket disconnected');
            setConnected(false);
            setConnecting(false);
        };

        const handleConnectError = () => {
            console.log('Socket connection error');
            setConnected(false);
            setConnecting(false);
        };

        // Add a timeout to handle cases where connection might be stuck
        const connectionTimeout = setTimeout(() => {
            if (!socket.connected) {
                console.log('Connection timeout - assuming disconnected');
                setConnected(false);
                setConnecting(false);
            }
        }, 10000); // 10 second timeout

        // Listen for connection events
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('connect_error', handleConnectError);

        // Cleanup
        return () => {
            clearTimeout(timeoutId);
            clearTimeout(connectionTimeout);
            socket.off('connect', handleConnect);
            socket.off('disconnect', handleDisconnect);
            socket.off('connect_error', handleConnectError);
        };
    }, []);

    const value = {
        connected,
        connecting,
        isOnline: connected && !connecting
    };

    return (
        <ConnectionContext.Provider value={value}>
            {children}
        </ConnectionContext.Provider>
    );
};
