'use client';
import { useEffect } from 'react';
import { socket } from '../socket';

const applyTitle = (name) => { if (name) document.title = name; };

export default function TitleSync() {
    useEffect(() => {
        const handleTester = (data) => applyTitle(data?.name);
        const handleState  = (data) => applyTitle(data?.tester?.name);
        socket.on('tester', handleTester);
        socket.on('state',  handleState);
        return () => {
            socket.off('tester', handleTester);
            socket.off('state',  handleState);
        };
    }, []);

    return null;
}
