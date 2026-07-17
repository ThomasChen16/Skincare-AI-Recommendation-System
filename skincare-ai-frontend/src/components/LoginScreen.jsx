// design for login in page
import { useState } from 'react'

// login screen compoennt that accepts onLogin prop
function LoginScreen({ onLogin }) {
    // state variables
    const [userId, setUserId] = useState(null)
    const [name, setName] = useState(null)
    const [error, setError] = useState(null)

    // when login is clicked
    async function handleLogin(e) {
        // prevent default form submission
        e.preventDefault()
        
        // call onLogin callback with the data
        onLogin(data)
}

    // Javascript object
    return (
        <div className="login-screen">
            <h1>Welcome to Skin Assistant</h1>
            <form onSubmit={handleLogin}>
                <div>
                    <label>User ID:</label>
                    <input type='text' placeholder="Enter your User ID" value={userId} onChange={(e) => setUserId(e.target.value)} required/>
                </div>
                <div>
                    <label>Name:</label>
                    <input type='text' placeholder="Enter your name" value={name} onChange={(e) => setName(e.target.value)} required/>
                </div>
                <button type='submit'>Login / Create Account</button>
                {error && <p className='error'>{error}</p>}
            </form>
        </div>
    )
}

// export the component so it can used in other files
export default LoginScreen
