// navigation bar shown at the top of every logged-in screen.
// Dumb component: receives the active screen (activeScreen), a callback
// for tab clicks (onNavigate), and whether the Shop tab is usable (hasRoutine).
function NavBar({ activeScreen, onNavigate, hasRoutine}) {
    const tabs = [
        { key: 'chat',      label: 'Chat' },
        { key: 'routine',   label: 'Routine' },
        { key: 'shop',      label: 'Shop' }
    ]

    return (
        <nav className='navbar'>
            {tabs.map((tab) => {
                const isActive = activeScreen === tab.key
                const isLocked = tab.key === 'shop' && !hasRoutine
                return (
                    <button
                        key={tab.key}
                        type='button'
                        className={`nav-tab${isActive ? ' active' : ''}${isLocked ? ' locked' : ''}`}
                        onClick={() => onNavigate(tab.key)}
                    >
                        {tab.label}
                        {isLocked && <span className='nav-badge'>no routine yet</span>}
                    </button>
                )
            })}
        </nav>
    )
}

export default NavBar