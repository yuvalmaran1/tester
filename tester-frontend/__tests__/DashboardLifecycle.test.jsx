import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import Home from '../app/page';
import { socket } from '../app/socket';

jest.mock('../app/socket', () => {
    const React = require('react');
    const mockedSocket = {
        emit: jest.fn(),
        on: jest.fn(),
        off: jest.fn(),
    };
    mockedSocket.emit.mockImplementation(() => mockedSocket);
    return {
        socket: mockedSocket,
        SocketContext: React.createContext(mockedSocket),
    };
});

jest.mock('../app/contexts/ConnectionContext', () => ({
    useConnection: () => ({ connected: true, connecting: false, isOnline: true }),
}));

jest.mock('../app/components/LoginDialog', () => () => null);
jest.mock('../app/components/LogModal', () => () => null);
jest.mock('../app/components/TestDialog', () => () => null);
jest.mock('../app/components/TestResultRow', () => () => null);

test('dashboard unmount does not treat the socket as an effect cleanup', () => {
    const { unmount } = render(<Home />);

    expect(socket.emit).toHaveBeenCalledWith('get_state');
    expect(() => unmount()).not.toThrow();
});