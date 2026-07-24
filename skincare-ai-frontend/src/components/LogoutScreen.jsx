// logout design with goodbye message and unique ID for future login

// displays goodbye message and user's unique ID
// - setMode: function to change the mode
// - error: error message if logout failed
// - unique_id: user's unique ID to display for future login reference
// - name: user's name for personalized goodbye message
function LogoutScreen({ setMode, error, unique_id, name }) {

    // handler function for returning to login screen
    function handleBacktoLogin() {
        setMode('login')
    }

    // JSX return statement
    return (
        <div className="logout-screen">
            <h1>Goodbye, {name}!</h1>
            <div className='logout-details'>
                <p>Your unique ID is: </p>
                <div className='unique-id-display'>{unique_id}</div>
                <p className='save-hint'>Save this ID to login later</p>
            </div>
            <button onClick={handleBacktoLogin}>Back to Login</button>

            {error && <p className='error'>{error}</p>}
        </div>
    )
}

// export the component so it can be used in other files
export default LogoutScreen