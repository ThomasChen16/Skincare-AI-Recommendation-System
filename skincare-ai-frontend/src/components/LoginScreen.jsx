// design for login in page
import { useState } from 'react'

// login screen component that accepts onLogin prop
function LoginScreen({ onLogin, mode, setMode, error, generatedId }) {
    // state variables
    const [userId, setUserId] = useState('')
    const [name, setName] = useState('')

    // handle login for existing users
    async function handleLogin(e) {
        // prevent default form submission
        e.preventDefault()

        // call onLogin callback with form data
        await onLogin({
            type: 'login',
            unique_id: userId,
            name: name || 'User'
        })
    }

    // handle create account for new users
    async function handleCreateAccount(e) {
        // prevent default form submission
        e.preventDefault()

        // call onLogin callback with form data
        await onLogin({
            type: 'create',
            name: name
        })
    }

    // Javascript object
    return (
        <div className="login-screen">
            <div className="login-layout">
                {/* Hero panel with photo */}
                <div className="login-hero">
                    <img src="/pictures/skincare-pic1.jpg" alt="Skincare products" />
                    <div className="login-hero-overlay">
                        <h1>Welcome to Skin Assistant</h1>
                        <p>Personalized skincare routines, powered by AI. Share your skin type, concerns and goals and we'll build a routine just for you.</p>
                    </div>
                </div>

                {/* Form panel */}
                <div className="login-panel">
            {!generatedId ? (
                <>
                    {/* Toggle between login and create account */}
                    <div className="login-toggle">
                        <button 
                            type="button"
                            className={mode === 'login' ? 'active' : ''}
                            onClick={() => setMode('login')}
                        >
                            Login
                        </button>
                        <button 
                            type="button"
                            className={mode === 'create' ? 'active' : ''}
                            onClick={() => setMode('create')}
                        >
                            Create Account
                        </button>
                    </div>

                    {mode === 'login' ? (
                        <form onSubmit={handleLogin}>
                            <div>
                                <label>User ID:</label>
                                <input 
                                    type='text' 
                                    placeholder="Enter your User ID" 
                                    value={userId} 
                                    onChange={(e) => setUserId(e.target.value)} 
                                    required
                                />
                            </div>
                            <div>
                                <label>Name:</label>
                                <input 
                                    type='text' 
                                    placeholder="Enter your name" 
                                    value={name} 
                                    onChange={(e) => setName(e.target.value)} 
                                    required
                                />
                            </div>
                            <button type='submit'>Login</button>
                        </form>
                    ) : (
                        <form onSubmit={handleCreateAccount}>
                            <div>
                                <label>Your Name:</label>
                                <input 
                                    type='text' 
                                    placeholder="Enter your name" 
                                    value={name} 
                                    onChange={(e) => setName(e.target.value)} 
                                    required
                                />
                            </div>
                            <button type='submit'>Create Account</button>
                            <p className="create-hint">We'll generate a unique ID for you</p>
                        </form>
                    )}
                    
                    {error && <p className='error'>{error}</p>}
                </>
            ) : (
                <div className="created-success">
                    <h2>Account Created!</h2>
                    <p>Your unique ID is:</p>
                    <div className="generated-id">{generatedId}</div>
                    <p className="save-hint">Save this ID to access your profile later</p>
                </div>
            )}
                </div>
            </div>
        </div>
    )
}

// export the component so it can used in other files
export default LoginScreen