import { describe, it, expect, vi } from 'vitest';
import { createRoot } from 'react-dom/client';

vi.mock('react-dom/client', () => ({
    createRoot: vi.fn(() => ({ render: vi.fn() }))
}));
import UserPage from '../src/UserPage';
import UserContext from '../src/shared/UserContext';

const renderWithContext = (element: JSX.Element, value: any): void => {
    const container = {} as any;
    createRoot(container).render(
        <UserContext.Provider value={value}>{element}</UserContext.Provider>
    );
};

describe.skip('UserPage', () => {
    it('toggles email display', () => {
        const value = {
            userData: { displayEmail: false } as any,
            setUserData: vi.fn(),
            clearUserData: vi.fn(),
        };
        const container = renderWithContext(<UserPage />, value);
        const input = container.querySelector('input') as HTMLInputElement;
        expect(input.checked).toBe(false);
        input.dispatchEvent(new Event('click', { bubbles: true }));
        expect(value.setUserData).toHaveBeenCalledWith({ ...value.userData, displayEmail: true });
    });
});
